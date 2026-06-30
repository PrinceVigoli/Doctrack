"""
notifications/service.py
─────────────────────────────────────────────────────────────
Dual-mode push notification service:
  1. Expo Push API  — for React Native / Expo Go devices (development)
  2. Firebase FCM HTTP v1 — for production Android / iOS builds

Usage:
    from notifications.service import notify_user, notify_document_event

    notify_user(user, "Title", "Body", data={"doc_id": 5})
    notify_document_event(document, event="forwarded", actor=request.user)
"""
import logging
import requests
from django.conf import settings
from .models import DeviceToken, NotificationLog

logger = logging.getLogger(__name__)

# ── Expo Push API ─────────────────────────────────────────────────────────────
EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def _send_expo(tokens: list[str], title: str, body: str, data: dict) -> tuple[int, int]:
    """Send via Expo Push API. Returns (sent, failed)."""
    if not tokens:
        return 0, 0

    messages = [
        {
            "to":        token,
            "title":     title,
            "body":      body,
            "data":      data,
            "sound":     "default",
            "badge":     1,
            "priority":  "high",
            "channelId": "doctrack",
        }
        for token in tokens
    ]

    try:
        res = requests.post(
            EXPO_PUSH_URL,
            json=messages,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=10,
        )
        res.raise_for_status()
        results = res.json().get("data", [])
        sent    = sum(1 for r in results if r.get("status") == "ok")
        failed  = len(results) - sent
        return sent, failed
    except Exception as e:
        logger.error(f"Expo push error: {e}")
        return 0, len(tokens)


# ── Firebase FCM HTTP v1 ───────────────────────────────────────────────────────

def _get_fcm_access_token() -> str:
    """
    Obtain a short-lived OAuth2 access token for the FCM HTTP v1 API.
    Reads credentials from FCM_SERVICE_ACCOUNT_JSON env var (JSON string or file path).
    Returns empty string if not configured.
    """
    sa_source = getattr(settings, 'FCM_SERVICE_ACCOUNT_JSON', '')
    if not sa_source:
        return ''

    try:
        import json
        import google.auth.transport.requests
        import google.oauth2.service_account

        # Accept either a raw JSON string or a file path
        try:
            sa_info = json.loads(sa_source)
        except (json.JSONDecodeError, ValueError):
            with open(sa_source) as f:
                sa_info = json.load(f)

        credentials = google.oauth2.service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=['https://www.googleapis.com/auth/firebase.messaging'],
        )
        credentials.refresh(google.auth.transport.requests.Request())
        return credentials.token

    except Exception as e:
        logger.error(f"FCM access token error: {e}")
        return ''


def _send_fcm(tokens: list[str], title: str, body: str, data: dict) -> tuple[int, int]:
    """
    Send via Firebase FCM HTTP v1 API.
    Requires FCM_PROJECT_ID and FCM_SERVICE_ACCOUNT_JSON settings.
    Returns (sent, failed).
    """
    project_id = getattr(settings, 'FCM_PROJECT_ID', '')
    if not project_id or not tokens:
        return 0, 0

    access_token = _get_fcm_access_token()
    if not access_token:
        logger.warning("FCM skipped: could not obtain access token.")
        return 0, len(tokens)

    url     = f'https://fcm.googleapis.com/v1/projects/{project_id}/messages:send'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type':  'application/json',
    }

    sent, failed = 0, 0
    for token in tokens:
        payload = {
            'message': {
                'token': token,
                'notification': {'title': title, 'body': body},
                'data': {k: str(v) for k, v in data.items()},
                'android': {'priority': 'high'},
                'apns':    {'headers': {'apns-priority': '10'}},
            }
        }
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            if res.status_code == 200:
                sent += 1
            else:
                logger.error(
                    f"FCM error for token ...{token[-10:]}: "
                    f"{res.status_code} {res.text[:200]}"
                )
                failed += 1
        except Exception as e:
            logger.error(f"FCM request error: {e}")
            failed += 1

    return sent, failed


# ── Public API ────────────────────────────────────────────────────────────────

def notify_user(user, title: str, body: str, data: dict = None,
                document=None) -> NotificationLog:
    """
    Send push notification to all active devices of a user.
    Creates a NotificationLog entry regardless of outcome.
    """
    data = data or {}
    log  = NotificationLog(
        recipient       = user,
        title           = title,
        body            = body,
        data            = data,
        document_id     = document.id if document else None,
        tracking_number = document.tracking_number if document else "",
    )

    tokens_qs = DeviceToken.objects.filter(user=user, is_active=True)
    if not tokens_qs.exists():
        log.status    = NotificationLog.Status.FAILED
        log.error_msg = "No active device tokens."
        log.save()
        return log

    expo_tokens = list(tokens_qs.filter(platform="expo").values_list("token", flat=True))
    fcm_tokens  = list(tokens_qs.exclude(platform="expo").values_list("token", flat=True))

    sent, failed = 0, 0
    s, f = _send_expo(expo_tokens, title, body, data)
    sent += s; failed += f
    s, f = _send_fcm(fcm_tokens, title, body, data)
    sent += s; failed += f

    log.status = NotificationLog.Status.SENT if sent > 0 else NotificationLog.Status.FAILED
    if failed:
        log.error_msg = f"{failed} device(s) failed to receive."
    log.save()
    return log


# ── Document event helpers ────────────────────────────────────────────────────

EVENT_TEMPLATES = {
    "submitted": (
        "📄 Document Submitted",
        "Your document '{title}' has been received. Tracking: {tracking_number}",
    ),
    "forwarded": (
        "➡️ Document Forwarded",
        "'{title}' has been forwarded to {office}. Tracking: {tracking_number}",
    ),
    "in_review": (
        "🔍 Document Under Review",
        "'{title}' is now being reviewed. Tracking: {tracking_number}",
    ),
    "approved": (
        "✅ Document Approved",
        "Great news! '{title}' has been approved. Tracking: {tracking_number}",
    ),
    "rejected": (
        "❌ Document Rejected",
        "'{title}' was rejected. Please check comments. Tracking: {tracking_number}",
    ),
    "returned": (
        "↩️ Document Returned",
        "'{title}' has been returned for revision. Tracking: {tracking_number}",
    ),
    "completed": (
        "🎉 Document Completed",
        "'{title}' has been fully processed. Tracking: {tracking_number}",
    ),
    "commented": (
        "💬 New Comment",
        "A comment was added to '{title}'. Tracking: {tracking_number}",
    ),
}


def notify_document_event(document, event: str, actor=None, office=None):
    """
    Notify the document submitter about a status change or action.
    Called from the Celery push_document_event task.
    """
    if not document.submitted_by:
        return

    # Don't notify the actor about their own action
    if actor and actor.id == document.submitted_by.id:
        return

    template = EVENT_TEMPLATES.get(event)
    if not template:
        return

    title_tpl, body_tpl = template
    office_name = office.name if office else (
        document.current_office.name if document.current_office else "—"
    )

    body = body_tpl.format(
        title           = document.title[:50],
        tracking_number = document.tracking_number,
        office          = office_name,
        actor           = actor.get_full_name() if actor else "—",
    )

    data = {
        "document_id":     document.id,
        "tracking_number": document.tracking_number,
        "event":           event,
        "screen":          "DocumentDetail",
    }

    notify_user(
        user     = document.submitted_by,
        title    = title_tpl,
        body     = body,
        data     = data,
        document = document,
    )
