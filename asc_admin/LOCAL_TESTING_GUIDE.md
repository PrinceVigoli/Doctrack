# ASC DocTrack — Local Testing Guide

A complete step-by-step guide to run the full system on your own computer.

---

## What You Need

| Tool | Version | Download |
|---|---|---|
| Python | 3.10+ | python.org |
| Node.js | 18+ | nodejs.org |
| Git (optional) | any | git-scm.com |
| Expo Go app | latest | Play Store / App Store |
| A phone + PC on the same Wi-Fi | — | — |

---

## PART 1 — Django Backend (API + AI)

### Step 1 — Extract the project

Unzip `ASC_DocTrack_FINAL.zip`. You'll get three folders:

```
ASC_DocTrack_FINAL/
├── asc_doctrack/     ← Django backend
├── asc_mobile/       ← React Native app
└── asc_admin/        ← Web admin panel
```

### Step 2 — Create a virtual environment

Open a terminal, go into the backend folder:

```bash
cd asc_doctrack

# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Mac / Linux:
source venv/bin/activate
```

You'll see `(venv)` at the start of the terminal line. Keep this terminal open.

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs Django, DRF, scikit-learn, and all other packages. Takes 1–2 minutes.

### Step 4 — Set up the `.env` file

The project already has a `.env` file. Open it and check these values:

```
SECRET_KEY=asc-doctrack-dev-secret-key-change-in-production
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
```

For local testing, these defaults work as-is. No changes needed.

### Step 5 — Run migrations

```bash
python manage.py migrate
```

Expected output ends with:
```
Applying notifications.0001_initial... OK
```

### Step 6 — Train the AI classifier

```bash
python manage.py train_classifier
```

Expected output:
```
Classifier trained on 159 samples → classifier/models/doc_classifier.pkl
Training accuracy: 159/159 (100%)
```

### Step 7 — Seed demo data

```bash
python manage.py shell -c "
from accounts.models import User, Office
from documents.models import DocumentType

# Offices
for name, code in [
    ('Registrar', 'REG'), ('VPAA', 'VPAA'), ('Research Office', 'RO'),
    ('Finance Office', 'FO'), ('Human Resource', 'HR'),
    ('Office of the President', 'OP'), ('Luna Campus Admin', 'LCA'),
]:
    Office.objects.get_or_create(name=name, defaults={'code': code})

# Document types
for name, code in [
    ('Memorandum','MEMO'), ('Request Letter','REQ'), ('Report','RPT'),
    ('Research Proposal','RPROP'), ('Certificate','CERT'),
    ('Purchase Request','PR'), ('Travel Order','TO'), ('Leave Form','LF'),
]:
    DocumentType.objects.get_or_create(name=name, defaults={'code': code})

# Admin user
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@asc.edu.ph', 'Admin@1234',
        first_name='System', last_name='Admin', role='admin')

# Demo staff user
if not User.objects.filter(username='staff1').exists():
    office = Office.objects.get(code='RO')
    u = User(username='staff1', email='staff1@asc.edu.ph',
             first_name='Maria', last_name='Santos', role='staff', office=office)
    u.set_password('Staff@1234')
    u.save()

print('Done! Offices:', Office.objects.count(), '| Types:', DocumentType.objects.count(), '| Users:', User.objects.count())
"
```

### Step 8 — Start the Django server

```bash
python manage.py runserver
```

You should see:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-C.
```

**Leave this terminal open and running.**

### Step 9 — Verify the API is working

Open your browser and go to:

| URL | What you should see |
|---|---|
| `http://127.0.0.1:8000/api/auth/offices/` | Needs login (401 error — correct!) |
| `http://127.0.0.1:8000/admin/` | Django admin login page |

Log into Django admin:
- URL: `http://127.0.0.1:8000/admin/`
- Username: `admin`
- Password: `Admin@1234`

You should see the full admin interface with Users, Offices, Documents, etc.

---

## PART 2 — Admin Web Panel (Browser)

No installation needed — it's plain HTML.

### Step 1 — Update the API URL

Open `asc_admin/js/api.js` and check line 2:

```js
const BASE_URL = 'http://127.0.0.1:8000/api';
```

This is already correct for local testing. No change needed.

### Step 2 — Open the admin panel

Just double-click `asc_admin/login.html` to open it in your browser.

OR open directly:
```
file:///path/to/asc_admin/login.html
```

### Step 3 — Log in

- Username: `admin`
- Password: `Admin@1234`

You should land on the **Dashboard** page. Since no documents exist yet, all counts will be zero — that's expected.

### Quick browser test

1. Click **Documents** in the sidebar → should show empty table
2. Click **Users** → should show 2 users (admin, staff1)
3. Click **Offices** → should show 7 offices
4. Click **AI Classifier** → type something in the Live Test box → should predict a category

---

## PART 3 — Mobile App (Expo)

### Step 1 — Install Expo CLI

Open a **new terminal** (keep the Django terminal running):

```bash
npm install -g expo-cli
```

### Step 2 — Install app dependencies

```bash
cd asc_mobile
npm install
```

### Step 3 — Find your computer's local IP address

The mobile app needs your PC's IP, not `localhost` (your phone can't reach `localhost`).

```bash
# Windows:
ipconfig
# Look for: IPv4 Address . . . . . . 192.168.x.x

# Mac:
ipconfig getifaddr en0

# Linux:
hostname -I
```

Write down your IP — e.g. `192.168.1.105`

### Step 4 — Update the API URL in the mobile app

Open `asc_mobile/src/api/client.js` and change line 3:

```js
// Change this:
export const BASE_URL = 'http://127.0.0.1:8000/api';

// To your actual IP:
export const BASE_URL = 'http://192.168.1.105:8000/api';
```

### Step 5 — Allow Django to accept connections from your phone

Open `asc_doctrack/.env` and add your IP to ALLOWED_HOSTS:

```
ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.105
```

Then **restart the Django server** with:

```bash
# Stop it first with Ctrl+C, then:
python manage.py runserver 0.0.0.0:8000
```

The `0.0.0.0` makes Django listen on all network interfaces (so your phone can reach it).

### Step 6 — Install Expo Go on your phone

- Android: [Play Store → "Expo Go"](https://play.google.com/store/apps/details?id=host.exp.exponent)
- iPhone: [App Store → "Expo Go"](https://apps.apple.com/app/expo-go/id982107779)

**Your phone and computer must be on the same Wi-Fi network.**

### Step 7 — Start the Expo development server

```bash
cd asc_mobile
npx expo start
```

You'll see a QR code in the terminal like this:

```
› Metro waiting on exp://192.168.1.105:8081
› Scan the QR code above with Expo Go (Android) or the Camera app (iOS)

▄▄▄▄▄▄▄▄▄▄▄▄▄
█ ▄▄▄▄▄ █▀▄▀ █
█ █   █ █▄▀▀ █
█ █▄▄▄█ █ ▀▄ █
▀▀▀▀▀▀▀▀▀▀▀▀▀
```

### Step 8 — Open the app on your phone

- **Android**: Open Expo Go → tap "Scan QR Code" → scan the QR
- **iPhone**: Open the Camera app → point at the QR code → tap the Expo Go banner

The app will build and load in about 30 seconds.

### Step 9 — Log in on the mobile app

- Username: `admin` / Password: `Admin@1234`
- Or: `staff1` / `Staff@1234`

You should see the Dashboard screen.

---

## PART 4 — End-to-End Test

Now test the full flow from mobile → backend → admin panel.

### Test 1: Submit a document

1. On the mobile app, tap **Documents** tab
2. Tap the **＋** button (green circle, bottom right)
3. Fill in:
   - Title: `Research Proposal on AI Integration in ASC`
   - Description: `A study on the use of AI tools in academic processes`
   - Priority: `High`
4. Tap **Attach a file** → tap OK (simulated for now)
5. Tap **Submit Document**

**Expected result:**
- Success alert shows tracking number (e.g. `ASC-202606-A1B2C3`)
- AI label shown: `Research Proposal`
- You're taken to the document detail screen

### Test 2: Check it in the admin panel

1. Go back to `asc_admin/documents.html` in your browser
2. Click **↻ Refresh**
3. You should see the new document appear in the table
4. Click the 👁 icon to open it
5. You should see the AI classification and tracking timeline

### Test 3: Update document status (admin)

1. In the document detail modal, select **Approved** from the status dropdown
2. Add a note: `Endorsed to Research Office`
3. Click **Update**

**Expected result:**
- Status badge changes to green "approved"
- Tracking timeline shows the new action

### Test 4: Check the update on mobile

1. On the mobile app, go to **Documents** tab
2. Pull down to refresh
3. The document should now show **approved** status badge
4. Tap the document → scroll to **Tracking History** → see the full timeline

### Test 5: Dashboard stats

1. On mobile, tap **Dashboard** tab → pull down to refresh
2. You should see:
   - Total: 1
   - Approved: 1
   - AI Document Types bar showing "Research Proposal"
3. In the admin panel, check `index.html` → refresh → same stats

---

## PART 5 — Test the AI Classifier

### From the admin panel

1. Open `asc_admin/ai.html`
2. In the **Live Classification Test** box, type:
   - `"Memo re Flag Ceremony Attendance"` → should predict **Memorandum**
   - `"Application for Sick Leave"` → should predict **Leave Form**
   - `"PR: Procurement of Printer Ink"` → should predict **Purchase Request**
   - `"Trip Ticket for Tuguegarao Seminar"` → should predict **Travel Order**

### From the Django shell

```bash
cd asc_doctrack
python manage.py shell

# Inside the shell:
from classifier.service import classify_document

class Doc:
    def __init__(self, t): self.title=t; self.description=''

tests = [
    "Memorandum re Submission of IPCR Forms",
    "Request Letter for Financial Assistance",
    "Quarterly Accomplishment Report",
    "Research Proposal: Digital Literacy Study",
    "Certificate of Participation Leadership Summit",
    "Purchase Request Office Supplies",
    "Travel Order CHED Conference",
    "Leave Application Vacation",
]

for t in tests:
    label, conf = classify_document(Doc(t))
    print(f"{label:<22} ({conf:.0%})  ← {t}")

exit()
```

---

## Troubleshooting

### "Connection refused" on the mobile app

- Make sure Django is running with `0.0.0.0:8000` not `127.0.0.1:8000`
- Double-check your IP in `client.js` matches `ipconfig` / `ifconfig`
- Make sure phone and PC are on the same Wi-Fi

### Admin panel shows CORS error in browser console

- Open `asc_doctrack/config/settings.py`
- Make sure `CORS_ALLOW_ALL_ORIGINS = DEBUG` is `True` (it is by default in dev)
- Restart Django

### "Expo Go" shows "Network response timed out"

- Restart both `npx expo start` and `python manage.py runserver 0.0.0.0:8000`
- Disable your PC firewall temporarily to test

### Django says "DisallowedHost"

- Add your IP to `ALLOWED_HOSTS` in `.env`
- Restart Django

### Mobile app QR code doesn't scan

- Try pressing `w` in the Expo terminal to open in browser instead
- Or manually enter the URL in Expo Go: `exp://192.168.1.105:8081`

### "Module not found" on npm install

```bash
cd asc_mobile
rm -rf node_modules
npm install --legacy-peer-deps
```

---

## All Running? Here's Your Setup

```
Terminal 1:  Django backend     → http://127.0.0.1:8000
Terminal 2:  Expo dev server    → exp://192.168.x.x:8081

Browser tab 1:  Admin panel     → asc_admin/index.html
Browser tab 2:  Django admin    → http://127.0.0.1:8000/admin/

Phone:  Expo Go app             → ASC DocTrack mobile app

Test accounts:
  admin  / Admin@1234  (admin role — sees everything)
  staff1 / Staff@1234  (staff role — Research Office)
```
