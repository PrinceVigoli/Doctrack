# ASC DocTrack — React Native Mobile App

## Requirements
- Node.js 18+
- Expo CLI: `npm install -g expo-cli`
- Expo Go app on your Android/iOS device (for testing)

## Setup
```bash
npm install
npx expo start
```
Scan the QR code with Expo Go on your phone.

## Connect to Django Backend
Edit `src/api/client.js`:
```js
export const BASE_URL = 'http://YOUR_PC_IP:8000/api';
```
Make sure Django is running: `python manage.py runserver 0.0.0.0:8000`

## Screens
| Screen | Path |
|--------|------|
| Login | src/screens/auth/LoginScreen.js |
| Dashboard | src/screens/dashboard/DashboardScreen.js |
| Document List | src/screens/documents/DocumentListScreen.js |
| Document Detail | src/screens/documents/DocumentDetailScreen.js |
| Submit Document | src/screens/documents/SubmitDocumentScreen.js |
| Profile | src/screens/profile/ProfileScreen.js |

## Features
- JWT authentication (auto-refresh)
- Dashboard with status stats, AI label chart, office workload, recent activity
- Document list with search + status filters
- Document detail with full tracking timeline
- Submit document with file attachment + AI auto-classification preview
- Role-based UI (admin/staff/viewer)
- Pull-to-refresh on all list screens

## Default Login (dev)
- Username: `admin`
- Password: `Admin@1234`
