"""
classifier/routing.py
─────────────────────────────────────────────────────────────
Smart Routing Engine — Version 2

Learns from past TrackingLog forwarding history to suggest
the most likely destination office for a given document type.

How it works:
  1. Look at all FORWARDED actions in TrackingLog for the same doc_type (or ai_label)
  2. Count how often each (from_office → to_office) transition happens
  3. Return the top 3 most frequent destinations as ranked suggestions

Falls back to a static rule table if there isn't enough history yet.
"""
import logging
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

# ── Static fallback routing rules ────────────────────────────────────────────
# Format: { document_label: [most_likely_office_code, ...] }
# Used when there's not enough real routing history yet.

STATIC_ROUTING_RULES = {
    'Research Proposal':  ['RO', 'VPAA', 'OP'],
    'Memorandum':         ['LCA', 'VPAA', 'OP'],
    'Request Letter':     ['VPAA', 'FO', 'OP'],
    'Report':             ['VPAA', 'RO', 'LCA'],
    'Certificate':        ['REG', 'HR', 'VPAA'],
    'Purchase Request':   ['FO', 'VPAA', 'OP'],
    'Travel Order':       ['VPAA', 'HR', 'FO'],
    'Leave Form':         ['HR', 'VPAA', 'LCA'],
    'Complaint':          ['REC', 'HR', 'OP'],
    'Grievance':          ['REC', 'HR', 'VPAA'],
    'Communication Letter': ['LCA', 'VPAA', 'OP'],
}

MIN_HISTORY = 3   # minimum log entries before we trust learned routing


def suggest_routing(document, top_n: int = 3) -> list[dict]:
    """
    Return up to `top_n` office suggestions for where to forward `document`.

    Each suggestion:
      {
        'office_id':   int,
        'office_name': str,
        'office_code': str,
        'confidence':  float  (0–1),
        'source':      'learned' | 'rule',
        'count':       int  (times this route was taken, 0 if rule-based),
      }
    """
    from tracking.models import TrackingLog
    from accounts.models import Office

    label = document.ai_label or (document.doc_type.name if document.doc_type else None)
    doc_type_id = document.doc_type_id

    # ── 1. Try learned routing from history ───────────────────────────────
    logs = TrackingLog.objects.filter(
        action='forwarded',
        to_office__isnull=False,
    )

    if doc_type_id:
        logs = logs.filter(document__doc_type_id=doc_type_id)
    elif label:
        logs = logs.filter(document__ai_label=label)

    route_counts = Counter(
        log.to_office_id for log in logs.select_related('to_office')
        if log.to_office_id
    )

    if sum(route_counts.values()) >= MIN_HISTORY:
        total  = sum(route_counts.values())
        result = []
        for office_id, count in route_counts.most_common(top_n):
            try:
                office = Office.objects.get(pk=office_id)
                result.append({
                    'office_id':   office.id,
                    'office_name': office.name,
                    'office_code': office.code,
                    'confidence':  round(count / total, 2),
                    'source':      'learned',
                    'count':       count,
                })
            except Office.DoesNotExist:
                pass
        if result:
            return result

    # ── 2. Fall back to static rules ──────────────────────────────────────
    if not label:
        return []

    rule_codes = STATIC_ROUTING_RULES.get(label, [])
    if not rule_codes:
        return []

    result = []
    base_conf = 0.75
    for i, code in enumerate(rule_codes[:top_n]):
        try:
            office = Office.objects.get(code=code)
            result.append({
                'office_id':   office.id,
                'office_name': office.name,
                'office_code': office.code,
                'confidence':  round(base_conf - i * 0.15, 2),
                'source':      'rule',
                'count':       0,
            })
        except Office.DoesNotExist:
            pass

    return result
