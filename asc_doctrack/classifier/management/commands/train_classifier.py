from django.core.management.base import BaseCommand
from pathlib import Path
import pickle

class Command(BaseCommand):
    help = 'Train the document AI classifier'

    def handle(self, *args, **options):
        from sklearn.pipeline import Pipeline
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from classifier.training_data import TRAINING_SAMPLES

        texts  = [t for t, _ in TRAINING_SAMPLES]
        labels = [l for _, l in TRAINING_SAMPLES]

        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
            ('clf',   LogisticRegression(max_iter=1000, C=5.0)),
        ])
        pipeline.fit(texts, labels)

        model_dir  = Path(__file__).parent.parent.parent / 'models'
        model_dir.mkdir(exist_ok=True)
        model_path = model_dir / 'doc_classifier.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(pipeline, f)

        self.stdout.write(self.style.SUCCESS(
            f'Classifier trained on {len(texts)} samples → {model_path}'
        ))
        preds   = pipeline.predict(texts)
        correct = sum(p == l for p, l in zip(preds, labels))
        self.stdout.write(f'Training accuracy: {correct}/{len(labels)} ({correct/len(labels)*100:.0f}%)')
