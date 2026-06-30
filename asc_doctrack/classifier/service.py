"""
AI Document Classification Service
-----------------------------------
v1 uses a TF-IDF + Logistic Regression pipeline (scikit-learn).
It reads the document title + description and returns:
  (label: str, confidence: float 0-1)

Training data: stored in classifier/training_data.py
Model file:    classifier/models/doc_classifier.pkl

To retrain: python manage.py train_classifier
"""
import os
import pickle
import logging
from pathlib import Path

logger   = logging.getLogger(__name__)
MODEL_PATH = Path(__file__).parent / 'models' / 'doc_classifier.pkl'
_pipeline  = None   # module-level cache


def _load_pipeline():
    global _pipeline
    if _pipeline is None and MODEL_PATH.exists():
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
