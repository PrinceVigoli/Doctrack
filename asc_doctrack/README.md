# ASC Smart Document Tracking System — Django Backend
**Apayao State College – Luna Campus**

## Project Structure
```
asc_doctrack/
├── config/          # Django settings, root URLs, wsgi/asgi
├── accounts/        # Custom User, Office, auth endpoints
├── documents/       # Document model, upload, classify, forward
├── tracking/        # TrackingLog (immutable audit trail)
├── classifier/      # AI classification (TF-IDF + LR + HuggingFace scanner)
│   ├── service.py       ← local TF-IDF classifier
│   ├── scanner.py       ← HuggingFace vision-language OCR
│   ├── training_data.py ← add more training samples here
│   └── models/          ← trained model saved here (.pkl)
├── notifications/   # Push notifications (Expo + FCM v1) + Celery tasks
└── dashboard/       # Summary stats + recent activity feed
```

## Quick Start
```bash
cp .env.example .env      # fill in your values
pip install -r requirements.txt
python manage.py migrate
python manage.py train_classifier
python manage.py createsuperuser
python manage.py runserver
```

> **Never commit `.env`** — it is listed in `.gitignore`.
> Run `python manage.py createsuperuser` to create the initial admin account.

## Environment Variables
Copy `.env.example` to `.env` and fill in all required values:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | ✅ | Django secret key — generate with `python -c "import secrets; print(secrets.token_hex(50))"` |
| `DEBUG` | ✅ | `True` for dev, **`False` in production** |
| `DATABASE_URL` | prod | PostgreSQL URL; omit for SQLite dev fallback |
| `REDIS_URL` | prod | Redis URL for Celery + Channels; omit for in-memory dev fallback |
| `HF_API_TOKEN` | scan | HuggingFace API token for document scanner |
| `HF_MODEL` | scan | Vision model (default: `Qwen/Qwen2.5-VL-7B-Instruct`) |
| `FCM_PROJECT_ID` | push | Firebase project ID for FCM v1 push notifications |
| `FCM_SERVICE_ACCOUNT_JSON` | push | Firebase service account JSON string or file path |
| `EXPO_ACCESS_TOKEN` | push | Expo push notification token |
| `ALLOWED_HOSTS` | prod | Comma-separated allowed hostnames |
| `CORS_ALLOWED_ORIGINS` | prod | Comma-separated allowed frontend origins |

## API Endpoints
| Method | URL | Description |
|--------|-----|-------------|
| POST | /api/auth/register/ | Create user (Records Admin only) |
| POST | /api/auth/login/ | Login → JWT tokens |
| POST | /api/auth/refresh/ | Refresh access token |
| POST | /api/auth/logout/ | Blacklist refresh token |
| GET  | /api/auth/me/ | Current user profile |
| GET  | /api/auth/offices/ | List offices |
| GET  | /api/docs/ | List documents (filterable) |
| POST | /api/docs/ | Submit new document (any authenticated user) |
| GET  | /api/docs/{id}/ | Document detail + logs |
| POST | /api/docs/{id}/forward/ | Forward to another office |
| POST | /api/docs/{id}/update-status/ | Change status (Records Admin) |
| POST | /api/docs/{id}/comment/ | Add comment |
| POST | /api/docs/check-duplicate/ | Pre-submission duplicate check |
| GET  | /api/docs/{id}/routing-suggestions/ | AI routing suggestions |
| GET  | /api/docs/{id}/priority-suggestion/ | Auto priority detection |
| GET  | /api/docs/{id}/qr/ | QR code PNG for tracking number |
| POST | /api/docs/scan/ | HuggingFace Vision OCR scan |
| GET  | /api/dashboard/summary/ | Stats & charts data |
| GET  | /api/dashboard/activity/ | Recent activity feed |

## Roles
| Role | Can Do |
|------|--------|
| `superadmin` | Everything — all offices, all docs, user management |
| `records_officer` | Manage all documents (forward, status, classify, create users) |
| `program_chair` | Forward documents, view all docs in their department |
| `faculty` | Submit documents, view own submissions |

## AI Classifier
- **Local TF-IDF + Logistic Regression** (scikit-learn) — fast, offline, always available
- **HuggingFace Vision OCR** — `Qwen/Qwen2.5-VL-7B-Instruct` (or set `HF_MODEL`) — for scanning physical documents
- Retrain local model: `python manage.py train_classifier`
- Improve accuracy: add more samples to `classifier/training_data.py`

## WebSockets
- Document tracking: `ws://host/ws/docs/{tracking_number}/?token=JWT`
- User notifications: `ws://host/ws/notifications/?token=JWT`
- Requires Redis + Daphne (ASGI server)

## Running in Production
```bash
# Start ASGI server (handles HTTP + WebSockets)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Start Celery worker (push notifications + background classification)
celery -A config worker -l info
```
