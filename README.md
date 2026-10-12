# LiveTrack — Location / Camera / Mic Share Platform

A lightweight Flask web application for creating and managing token-based live-session links. Each link lets visitors choose whether to share their location, front camera, or microphone, with permission-based data sharing to your server dashboard.

🚀 Key Features:

- 🔗 Shareable token-based links
- 📍 Live GPS location updates
- 📷 Time-lapse photo capture
- 🎙️ Audio recording in chunks
- 📊 Real-time admin dashboard
- 💾 SQLite database for persistent storage
- 📱 Mobile-friendly themed landing pages
- 🗑️ Media management with photo and audio deletion

«🔐 Security & Privacy: Intended for authorized testing, personal devices, and legitimate use. Obtain informed consent before collecting anyone’s data, comply with applicable laws, and use only infrastructure you own or are authorized to test. Never collect data secretly or without permission.»

---

## 🌟 Features

* 🚀 Admin Dashboard Features

- 🛠️ Admin Panel: Create, manage, enable/disable, and revoke share links.
- 🔗 Individual Controls: Toggle Location, Camera, Microphone, and Battery separately for each link.
- 📍 Location: GPS tracking with live map, accuracy, speed, and altitude.
- 📷 Camera: Front-camera access with photos captured every 5 seconds.
- 🎙️ Microphone: Audio recording saved in 10-second intervals.
- ⚡ Battery Status: Monitor battery level and charging status.
- 🎨 Custom Landing Pages: Different page designs for location, camera, and microphone features.
- 🔐 Permission Control: Request browser permissions only for enabled features.
- 📊 Live Monitoring: View maps, reports, GPS accuracy history, media gallery, and battery status.
- 🗑️ Delete Media: Delete stored photos and audio recordings anytime to free up storage and prevent it from filling up.
- 💾 SQLite Database: Simple local database without an external database server.
- 🌐 Flexible Hosting: Compatible with HTTPS tunnels like ngrok, Localtonet, Cloudflare, and VPS hosting.
Storage Management: Built-in media deletion controls make it easy to remove unwanted or outdated files whenever needed, reducing the risk of storage filling up. Available storage still depends on the hosting environment.
---


## ⚙️ Setup (Local)

```bash
# 1. Clone & enter
git clone https://github.com/cji63671-arch/Swapnish-tracker-.git
cd Swapnish-tracker-

# 2. Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 3. Run
python app.py
```

Open **http://127.0.0.1:5000** → login with the default admin credentials:

| Username | Password |
|----------|----------|
| `Swapnish `  | `123456789` |

> ⚠️ **Change the default password** in `app.py` before any real use.

---

## 🔒 HTTPS (required for camera/mic/location)

🌐 Browser access to 📷 Camera, 🎙 Microphone, and 📍 Location requires a secure context (HTTPS or localhost). On a plain LAN IP, permissions may not work. Use a free tunnel or HTTPS host:

# Localtonet — forward local port 5000
localtonet
# Open dashboard → create HTTPS tunnel to 127.0.0.1:5000

# Or ngrok
ngrok http 5000

You'll get a public URL like "https://xxxx.localto.net". Use this HTTPS URL to open both the dashboard and shared links. Always open the dashboard through the tunnel URL when creating share links.

🗑️ Media Storage: Add an option to delete stored photos and audio recordings anytime, freeing up storage space when needed.
---


### 🔄 How the Visitor Flow Works

1. ⚡ Instant Loading: A themed page matching the link opens immediately without blocking overlays.

2. 👆 User Interaction: The visitor clicks the main button — Track Package, Join Call, or Start Recording.

3. 🔐 Native Permissions: The browser asks for permission only for the features enabled on that link.

4. 📡 Real-Time Data: After permission is granted, enabled features begin working:
   
   - 📍 GPS location updates continuously.
   - 📷 Camera captures a photo every 5 seconds.
   - 🎙️ Audio is recorded and uploaded in 10-second chunks.

5. 📊 Dashboard Sync: Approved data is sent to the server and displayed on the admin dashboard in real time.

## 📜 License

MIT — use responsibly and only with proper authorization.

---

## ⚠️ Responsibility

🔐 Disclaimer & Responsible Use

This project is intended for authorized security testing, personal device monitoring, and legitimate purposes only. You must comply with all applicable laws and obtain informed consent before collecting anyone’s location, photos, or audio. The author provides no warranty and accepts no liability for misuse or damages arising from the use of this project.
