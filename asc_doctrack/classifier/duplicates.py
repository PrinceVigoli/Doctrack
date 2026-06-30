"""
classifier/duplicates.py
─────────────────────────────────────────────────────────────
Duplicate Detection — Version 2

When a new document is submitted, compare it against recent
documents from the same origin office using TF-IDF cosine
similarity.

If similarity > THRESHOLD, flag as a potential duplicate.

Returns:
  {
    'is_duplicate':   bool,
    'confidence':     float,
    'similar_docs':   [
      {
        'id':               int,
        'tracking_number':  str,
        'title':            str,
        'similarity':       float,
        'submitted_at':     str,
        'status':           str,
      },
      ...
    ],
    'message': str,
  }
"""
import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.82   # flag if similarity >= this
LOOKBACK_DAYS        = 30     # only compare against last 30 days
MAX_CANDIDATES       = 200    # max docs to compare against (performance cap)
TOP_N                = 3      # return top N similar docs


def _vectorize(texts: list[str]):
    """TF-IDF vectorize a list of texts. Returns (matrix, vectorizer)."""
    from sklearn.feature_extraction.text import TfidfVectorizer
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)
    matrix     = vectorizer.fit_transform(texts)
    return matrix, vectorizer


def check_duplicates(document) -> dict:
    """
    Compare `document` against recent docs from the same office.
    Returns a dict with duplicate flag, confidence, and similar documents.
    """
    from documents.models import Document

    text = f"{document.title} {document.description}".strip()
    if not text:
        return _no_duplicate('Document has no text to compare.')

    # ── Fetch candidate documents ──────────────────────────────────────────
    since = timezone.now() - timedelta(days=LOOKBACK_DAYS)
    qs    = Document.objects.filter(created_at__gte=since)

    # Exclude the document itself (for re-checks after save)
    if document.pk:
        qs = qs.exclude(pk=document.pk)

    # Same office if available
    if document.origin_office_id:
        qs = qs.filter(origin_office_id=document.origin_office_id)

    candidates = list(qs.values('id', 'tracking_number', 'title',
                                 'description', 'created_at', 'status')[:MAX_CANDIDATES])

    if not candidates:
        return _no_duplicate('No recent documents to compare against.')

    # ── TF-IDF + cosine similarity ─────────────────────────────────────────
    try:
        from sklearn.metrics.pairwise import cosine_similarity

        candidate_texts = [
            f"{c['title']} {c['description'] or ''}".strip()
            for c in candidates
        ]
        all_texts  = [text] + candidate_texts
        matrix, _  = _vectorize(all_texts)
        new_vec    = matrix[0]
        cand_mat   = matrix[1:]
        scores     = cosine_similarity(new_vec, cand_mat)[0]

    except Exception as e:
        logger.warning(f"Duplicate detection error: {e}")
        return _no_duplicate('Similarity check failed — skipped.')

    # ── Collect similar docs above threshold ───────────────────────────────
    indexed  = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    similar  = []

    for idx, score in indexed[:TOP_N]:
        if score >= SIMILARITY_THRESHOLD:
            c = candidates[idx]
            similar.append({
                'id':              c['id'],
                'tracking_number': c['tracking_number'],
                'title':           c['title'],
                'similarity':      round(float(score), 3),
                'similarity_pct':  f"{round(float(score) * 100)}%",
                'submitted_at':    c['created_at'].strftime('%b %d, %Y') if c['created_at'] else '—',
                'status':          c['status'],
            })

    if similar:
        top_score = similar[0]['similarity']
        return {
            'is_duplicate': True,
            'confidence':   round(top_score, 3),
            'similar_docs': similar,
            'message': (
                f"⚠️ This document is {round(top_score*100)}% similar to "
                f"'{similar[0]['title']}' submitted on {similar[0]['submitted_at']}. "
                f"Please verify this is not a duplicate before proceeding."
            ),
        }

    return _no_duplicate('No similar documents found.')


def _no_duplicate(reason: str) -> dict:
    return {
        'is_duplicate': False,
        'confidence':   0.0,
        'similar_docs': [],
        'message':      reason,
    }
