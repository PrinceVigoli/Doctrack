"""
AI Document Classification Service
-----------------------------------
v1 uses a TF-IDF + Logistic Regression pipeline (scikit-learn).
It reads the document title + description and returns:
  (label: str, confidence: float 0-1)

Training data: stored in classifier/training_data.py
Model file:    classifier/models/doc_classifier.pkl

To retrain: python manage.py train_classifier

SECURITY: MODEL_PATH must always be a fixed, developer-controlled path —
never derive it from request data, a database value, or any other
user-influenced input. pickle.load() executes arbitrary code for whatever
bytes it's given, so this loader only trusts a file matching EXPECTED_SHA256
below. A mismatch (tampering, a swapped-in file, or a future "upload your
own model" feature that reuses this loader without updating the pin) is
treated as "no model available" — it logs an error and falls back to the
rule-based heuristics below rather than deserializing untrusted bytes.

`python manage.py train_classifier` prints the new file's SHA256 after
writing it; update EXPECTED_SHA256 to that value as a deliberate,
reviewed step whenever the model is intentionally retrained.
"""
import os
import pickle
import hashlib
import logging
from pathlib import Path

logger   = logging.getLogger(__name__)
MODEL_PATH = Path(__file__).parent / 'models' / 'doc_classifier.pkl'
_pipeline  = None   # module-level cache

# SHA256 of the currently-trusted classifier/models/doc_classifier.pkl.
# Update this constant (and only this constant) after a deliberate retrain.
EXPECTED_SHA256 = 'ed3278ee186aee2ade9be6584cf9cd735f72eb79c3365f3a6566118cfc6bc67d'


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _load_pipeline():
    global _pipeline
    if _pipeline is None and MODEL_PATH.exists():
        actual_hash = _file_sha256(MODEL_PATH)
        if actual_hash != EXPECTED_SHA256:
            logger.error(
                "Classifier model at %s failed its integrity check "
                "(expected sha256=%s, got %s). Refusing to unpickle it; "
                "falling back to heuristic classification. If this model "
                "was retrained on purpose, update EXPECTED_SHA256 in "
                "classifier/service.py.",
                MODEL_PATH, EXPECTED_SHA256, actual_hash,
            )
            return None
        with open(MODEL_PATH, 'rb') as f:
            _pipeline = pickle.load(f)
    return _pipeline


def classify_document(document) -> tuple[str, float]:
    """
    Given a Document instance, return (label, confidence).
    Falls back to rule-based heuristics if model is not trained yet.
    """
    text = f"{document.title} {document.description}".strip().lower()
    pipeline = _load_pipeline()

    if pipeline:
        try:
            label      = pipeline.predict([text])[0]
            proba      = pipeline.predict_proba([text])[0]
            confidence = float(max(proba))
            return label, confidence
        except Exception as e:
            logger.warning(f"Classifier error: {e}")

    # --- Fallback: keyword heuristics ---
    rules = [
        (['memorandum', 'memo', 'circular'],           'Memorandum'),
        (['request', 'application', 'appeal'],         'Request Letter'),
        (['report', 'narrative', 'accomplishment'],    'Report'),
        (['proposal', 'research', 'study', 'project'], 'Research Proposal'),
        (['certificate', 'certification'],             'Certificate'),
        (['purchase', 'procurement', 'requisition'],   'Purchase Request'),
        (['travel', 'itinerary', 'trip'],              'Travel Order'),
        (['leave', 'absence', 'vacation'],             'Leave Form'),
    ]
    for keywords, label in rules:
        if any(kw in text for kw in keywords):
            return label, 0.70   # heuristic confidence

    return 'Uncategorized', 0.0
