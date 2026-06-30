# ASC DocTrack — Deployment Guide
**Apayao State College – Luna Campus**
*Django Backend + React Native Mobile App + Admin Panel*

---

## 📋 What You're Deploying

| Component | Technology | Port |
|---|---|---|
| Django API | Python + Gunicorn | 8000 |
| Database | PostgreSQL | 5432 |
| Static/Media files | Nginx | 80 / 443 |
| Mobile App | Expo (React Native) | via Expo EAS |
| Admin Panel | Static HTML/CSS/JS | served by Nginx |

---

# OPTION A — Local Server at ASC (Ubuntu/Linux)

Best for: keeping data on-campus, no internet dependency, full control.

## Step 1 — Prepare the Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv \
    postgresql postgresql-contrib nginx git curl

# Create a dedicated user for the app
sudo adduser ascadmin
sudo usermod -aG sudo ascadmin
su - ascadmin
```

## Step 2 — Set Up PostgreSQL

```bash
sudo -u postgres psql

-- Inside psql:
CREATE DATABASE asc_doctrack;
CREATE USER asc_user WITH PASSWORD 'StrongPassword123!';
ALTER ROLE asc_user SET client_encoding TO 'utf8';
ALTER ROLE asc_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE asc_user SET timezone TO 'Asia/Manila';
GRANT ALL PRIVILEGES ON DATABASE asc_doctrack TO asc_user;
\q
```

## Step 3 — Deploy Django Backend

```bash
# Clone or copy your project to the server
mkdir -p /home/ascadmin/asc_doctrack
cd /home/ascadmin/asc_doctrack

# (Upload your zip and extract, or use git)
# unzip asc_doctrack_backend_v2.zip -d .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Create production .env
cat > .env << 'EOF'
SECRET_KEY=CHANGE-THIS-TO-A-LONG-RANDOM-STRING-50-CHARS
DEBUG=False
DATABASE_URL=postgresql://asc_user:StrongPassword123!@localhost/asc_doctrack
ALLOWED_HOSTS=192.168.1.100,doctrack.asc.edu.ph,localhost
FCM_SERVER_KEY=YOUR_FCM_SERVER_KEY_FROM_FIREBASE_CONSOLE
EOF

# Run migrations and setup
python manage.py migrate
python manage.py train_classifier
python manage.py collectstatic --noinput

# Create admin superuser
python manage.py createsuperuser
```

## Step 4 — Set Up Gunicorn (WSGI Server)

```bash
# Test gunicorn works
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Create systemd service
sudo nano /etc/systemd/system/asc_doctrack.service
```

Paste this into the file:

```ini
[Unit]
Description=ASC DocTrack Django API
After=network.target

[Service]
User=ascadmin
Group=www-data
WorkingDirectory=/home/ascadmin/asc_doctrack
ExecStart=/home/ascadmin/asc_doctrack/venv/bin/gunicorn \
    --access-logfile - \
    --workers 3 \
    --bind unix:/run/asc_doctrack.sock \
    config.wsgi:application
Restart=always
EnvironmentFile=/home/ascadmin/asc_doctrack/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable asc_doctrack
sudo systemctl start asc_doctrack
sudo systemctl status asc_doctrack   # Should show: active (running)
```

## Step 5 — Set Up Nginx

```bash
sudo nano /etc/nginx/sites-available/asc_doctrack
```

Paste this config:

```nginx
server {
    listen 80;
    server_name 192.168.1.100 doctrack.asc.edu.ph;

    # Django API
    location /api/ {
        include proxy_params;
        proxy_pass http://unix:/run/asc_doctrack.sock;
        client_max_body_size 20M;
    }

    location /admin/ {
        include proxy_params;
        proxy_pass http://unix:/run/asc_doctrack.sock;
    }

    # Static files (Django collectstatic)
    location /static/ {
        alias /home/ascadmin/asc_doctrack/staticfiles/;
    }

    # Media files (uploaded documents)
    location /media/ {
        alias /home/ascadmin/asc_doctrack/media/;
    }

    # Admin web panel (static HTML)
    location / {
        root /home/ascadmin/asc_admin;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/asc_doctrack /etc/nginx/sites-enabled/
sudo nginx -t          # Test config — should say: syntax is ok
sudo systemctl restart nginx

# Deploy admin panel
mkdir -p /home/ascadmin/asc_admin
# Upload asc_doctrack_admin.zip and extract here
# Update BASE_URL in asc_admin/js/api.js:
#   const BASE_URL = 'http://YOUR_SERVER_IP/api';
```

## Step 6 — Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

## Step 7 — Connect Mobile App to Local Server

Edit `src/api/client.js` in the mobile app:
```js
// Use your server's local IP (not localhost!)
export const BASE_URL = 'http://192.168.1.100/api';
```

---

# OPTION B — Railway (Free Cloud Hosting)

Best for: accessible from anywhere, no server to maintain, free tier available.

## Step 1 — Prepare

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
```

## Step 2 — Add Procfile & runtime

```bash
# In your asc_doctrack folder:
echo "web: gunicorn config.wsgi:application --bind 0.0.0.0:\$PORT" > Procfile
echo "python-3.11.0" > runtime.txt

# Add to requirements.txt:
echo "gunicorn" >> requirements.txt
echo "whitenoise" >> requirements.txt   # serves static files on Railway
```

Add WhiteNoise to `config/settings.py` MIDDLEWARE (after SecurityMiddleware):
```python
'whitenoise.middleware.WhiteNoiseMiddleware',
```
And add at the bottom:
```python
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

## Step 3 — Deploy to Railway

```bash
cd asc_doctrack
railway init          # creates a new project
railway add           # add PostgreSQL plugin (Railway provisions it automatically)

# Set environment variables in Railway dashboard or CLI:
railway variables set SECRET_KEY="your-long-secret-key"
railway variables set DEBUG="False"
railway variables set ALLOWED_HOSTS="your-app.railway.app"
railway variables set FCM_SERVER_KEY="your-fcm-key"

# Deploy
railway up
```

## Step 4 — Post-deploy Setup

```bash
railway run python manage.py migrate
railway run python manage.py train_classifier
railway run python manage.py createsuperuser
railway run python manage.py collectstatic --noinput
```

## Step 5 — Host Admin Panel on Netlify (free)

```bash
# Install Netlify CLI
npm install -g netlify-cli

cd asc_admin
# Update BASE_URL in js/api.js:
#   const BASE_URL = 'https://your-app.railway.app/api';

netlify deploy --prod --dir .
# Netlify gives you a free URL like: https://asc-doctrack-admin.netlify.app
```

## Step 6 — Connect Mobile App

```js
// src/api/client.js
export const BASE_URL = 'https://your-app.railway.app/api';
```

---

# OPTION C — Render (Free Cloud, Alternative to Railway)

Similar to Railway. Key differences:
- Free tier spins down after 15 min inactivity (wakes on request)
- Good for staging/demo environments

```bash
# render.yaml (place in project root)
cat > render.yaml << 'EOF'
services:
  - type: web
    name: asc-doctrack-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: ALLOWED_HOSTS
        value: "asc-doctrack-api.onrender.com"
    databases:
      - name: asc-doctrack-db
        databaseName: asc_doctrack
        user: asc_user
EOF
```

Then push to GitHub and connect the repo in render.com dashboard.

---

# 🔔 Firebase Push Notifications Setup

Required for production push notifications on real Android/iOS builds.

## Step 1 — Create Firebase Project

1. Go to [console.firebase.google.com](https://console.firebase.google.com)
2. Click **Add Project** → name it `ASC DocTrack`
3. Disable Google Analytics (not needed) → **Create Project**

## Step 2 — Get FCM Server Key

1. In Firebase Console → **Project Settings** (gear icon)
2. Click **Cloud Messaging** tab
3. Copy the **Server Key** (long string starting with `AAAA...`)
4. Add it to your `.env` file:
   ```
   FCM_SERVER_KEY=AAAAxxxxxx...your_key_here
   ```

## Step 3 — Configure Expo for Push Notifications

```bash
cd asc_mobile

# Install required packages
npx expo install expo-notifications expo-device

# Install EAS CLI for building
npm install -g eas-cli
eas login
eas build:configure
```

Update `app.json`:
```json
{
  "expo": {
    "name": "ASC DocTrack",
    "slug": "asc-doctrack",
    "plugins": [
      [
        "expo-notifications",
        {
          "icon": "./assets/icon.png",
          "color": "#1B4332",
          "sounds": []
        }
      ]
    ],
    "android": {
      "googleServicesFile": "./google-services.json",
      "package": "edu.asc.doctrack"
    },
    "ios": {
      "bundleIdentifier": "edu.asc.doctrack"
    }
  }
}
```

## Step 4 — Add google-services.json

1. In Firebase → **Project Settings** → **Your Apps** → **Add App** → Android
2. Package name: `edu.asc.doctrack`
3. Download `google-services.json`
4. Place it in the `asc_mobile/` root folder

## Step 5 — Build Production APK

```bash
cd asc_mobile

# Build Android APK (free, no Apple account needed)
eas build --platform android --profile preview

# After build completes, download the .apk from the EAS dashboard
# Install on Android phones via USB or share the download link
```

---

# 📱 Install App on Android Phones (Without Play Store)

```bash
# Enable "Install from Unknown Sources" on the Android phone:
# Settings → Security → Install Unknown Apps → Allow

# Option 1: Share via USB
adb install asc-doctrack.apk

# Option 2: Share the EAS download link
# Staff download the .apk directly on their phone and tap to install
```

---

# ✅ Post-Deployment Checklist

- [ ] Django API is running and accessible
- [ ] Admin panel opens and login works
- [ ] Database migrations applied
- [ ] AI classifier retrained (`python manage.py train_classifier`)
- [ ] Superuser created
- [ ] Offices seeded (via Django admin or shell)
- [ ] FCM_SERVER_KEY set in environment
- [ ] Mobile app BASE_URL points to production server
- [ ] Production APK built and installed on staff phones
- [ ] Test: submit a document and verify push notification arrives
- [ ] HTTPS/SSL configured (for production — use Let's Encrypt)

---

# 🔐 SSL/HTTPS (Production — Local Server)

```bash
sudo apt install certbot python3-certbot-nginx

# If you have a domain name:
sudo certbot --nginx -d doctrack.asc.edu.ph

# Auto-renew (already set up by certbot, verify with):
sudo certbot renew --dry-run
```

For a local-only server without a public domain, use a self-signed cert:
```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/asc_doctrack.key \
    -out /etc/ssl/certs/asc_doctrack.crt
```

---

# 🔄 Updating the System

```bash
# Pull new code, then:
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py train_classifier   # if training_data.py changed
python manage.py collectstatic --noinput
sudo systemctl restart asc_doctrack
```
