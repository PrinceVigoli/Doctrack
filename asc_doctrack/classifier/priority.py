"""
classifier/priority.py
─────────────────────────────────────────────────────────────
Auto Priority Detection — Version 2

Scans document title + description for urgency signals and
suggests a priority level automatically.

Three signals checked in order:
  1. URGENT keywords  → priority = 'urgent'
  2. HIGH keywords    → priority = 'high'
  3. Due date proximity → high if due ≤ 3 days, urgent if due today/overdue
  4. No signals       → priority = 'normal' (leave user's choice)

Returns:
  {
    'suggested_priority': 'urgent' | 'high' | 'normal',
    'reason': str,
    'signals_found': [str],
    'confidence': float,
  }
"""
import re
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

# ── Keyword lists ─────────────────────────────────────────────────────────────

URGENT_KEYWORDS = [
    # English
    'urgent', 'asap', 'immediately', 'emergency', 'critical', 'today only',
    'last day', 'final notice', 'deadline today', 'overdue', 'past due',
    'no extension', 'rush', 'top priority', 'highest priority',
    # Filipino/Tagalog
    'agad', 'agarang aksyon', 'araw na ito', 'huling araw', 'prayoridad',
    'kailangang-kailangan', 'napaka-urgent', 'pinaka-importante',
]

HIGH_KEYWORDS = [
    # English
    'high priority', 'important', 'action required', 'action needed',
    'please prioritize', 'time-sensitive', 'time sensitive', 'due soon',
    'respond immediately', 'requires immediate', 'attention required',
    'please act', 'kindly act', 'soonest', 'at the soonest',
    'within 24 hours', 'within 48 hours', 'within the day',
    'earliest possible', 'prioritize',
    # Filipino/Tagalog
    'kailangan agad', 'mahalaga', 'bigyang pansin', 'maagang aksyon',
    'sa lalong madaling panahon', 'alamin agad',
]


def detect_priority(document) -> dict:
    """
    Analyse a Document instance and return a priority suggestion.
    """
    text     = f"{document.title} {document.description}".lower().strip()
    signals  = []

    # ── Check urgent keywords ─────────────────────────────────────────────
    for kw in URGENT_KEYWORDS:
        if kw in text:
            signals.append(f'Keyword: "{kw}"')

    if signals:
        return {
            'suggested_priority': 'urgent',
            'reason': f'Urgency keywords detected in document text.',
            'signals_found': signals,
            'confidence': 0.88,
        }

    # ── Check high priority keywords ──────────────────────────────────────
    for kw in HIGH_KEYWORDS:
        if kw in text:
            signals.append(f'Keyword: "{kw}"')

    if signals:
        return {
            'suggested_priority': 'high',
            'reason': 'High-priority keywords detected.',
            'signals_found': signals,
            'confidence': 0.78,
        }

    # ── Check due date proximity ──────────────────────────────────────────
    if document.due_date:
        today     = date.today()
        days_left = (document.due_date - today).days

        if days_left <= 0:
            signals.append(f'Due date: {document.due_date} (overdue or today)')
            return {
                'suggested_priority': 'urgent',
                'reason': 'Document is overdue or due today.',
                'signals_found': signals,
                'confidence': 0.95,
            }
        elif days_left <= 3:
            signals.append(f'Due date: {document.due_date} ({days_left} days left)')
            return {
                'suggested_priority': 'high',
                'reason': f'Due in {days_left} day(s).',
                'signals_found': signals,
                'confidence': 0.90,
            }

    # ── Check for explicit priority mentions in text ───────────────────────
    priority_pattern = re.compile(
        r'\b(priority[\s:]+(?:1|one|high|urgent|top)|p1\b|p-1\b)', re.IGNORECASE
    )
    if priority_pattern.search(text):
        signals.append('Explicit priority mention in text')
        return {
            'suggested_priority': 'high',
            'reason': 'Explicit priority mention found.',
            'signals_found': signals,
            'confidence': 0.82,
        }

    # ── No signals found ──────────────────────────────────────────────────
    return {
        'suggested_priority': 'normal',
        'reason': 'No urgency signals detected.',
        'signals_found': [],
        'confidence': 0.60,
    }
