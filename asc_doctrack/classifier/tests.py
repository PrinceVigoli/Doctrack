"""
classifier/tests.py
───────────────────
Tests for Finding #5: pickle.load() without integrity verification.

Before the fix, _load_pipeline() unconditionally called pickle.load() on
whatever bytes were at MODEL_PATH. pickle.load() executes arbitrary code, so
if that path were ever pointed at attacker-controlled bytes (e.g. via a
future "upload a custom model" feature), it would be an RCE vector.

After the fix, _load_pipeline():
  1. Computes the SHA-256 of the file on disk.
  2. Compares it against EXPECTED_SHA256 (a constant pinned to the current
     trusted artifact).
  3. Logs an error and returns None (falling back to heuristics) on mismatch
     rather than deserializing untrusted bytes.

These tests verify all three behaviours, plus that the pinned constant in
service.py actually matches the file on disk (so a silently stale pin is
caught in CI before it reaches production).
"""
import hashlib
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase

from classifier.service import (
    EXPECTED_SHA256,
    MODEL_PATH,
    _file_sha256,
    _load_pipeline,
)


def _reset_pipeline_cache():
    """Reset the module-level _pipeline cache between tests."""
    import classifier.service as svc
    svc._pipeline = None


# ── _file_sha256 ──────────────────────────────────────────────────────────────

class FileSHA256Tests(TestCase):
    def test_hash_matches_direct_hashlib_computation(self):
        """_file_sha256 must produce the same result as a direct hashlib.sha256 run."""
        if not MODEL_PATH.exists():
            self.skipTest("Model file not present in this environment.")
        expected = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
        self.assertEqual(_file_sha256(MODEL_PATH), expected)

    def test_hash_is_64_hex_chars(self):
        """SHA-256 digest must always be a 64-character lowercase hex string."""
        if not MODEL_PATH.exists():
            self.skipTest("Model file not present in this environment.")
        digest = _file_sha256(MODEL_PATH)
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in digest))


# ── EXPECTED_SHA256 pin ───────────────────────────────────────────────────────

class ExpectedHashPinTests(TestCase):
    """
    The hardcoded EXPECTED_SHA256 constant must exactly match the file on disk.
    A mismatch here means either:
      (a) the model was retrained and the constant wasn't updated — the fix
          is to run `python manage.py train_classifier` and follow its
          instructions; or
      (b) the file was tampered with since the last deliberate retrain.
    Catching both in CI is the whole point of the pin.
    """

    def test_expected_sha256_matches_current_model_file(self):
        if not MODEL_PATH.exists():
            self.skipTest("Model file not present in this environment.")
        actual = _file_sha256(MODEL_PATH)
        self.assertEqual(
            actual, EXPECTED_SHA256,
            f"Model file hash mismatch.\n"
            f"  EXPECTED_SHA256 in service.py : {EXPECTED_SHA256}\n"
            f"  Actual hash of {MODEL_PATH.name}: {actual}\n"
            "Either the model was retrained without updating the pin, or the "
            "file was modified. Run `python manage.py train_classifier` and "
            "update EXPECTED_SHA256 in classifier/service.py."
        )


# ── _load_pipeline integrity gate ─────────────────────────────────────────────

class LoadPipelineIntegrityTests(TestCase):

    def setUp(self):
        _reset_pipeline_cache()

    def tearDown(self):
        _reset_pipeline_cache()

    def test_load_pipeline_succeeds_with_correct_hash(self):
        """_load_pipeline() returns a non-None pipeline when the hash matches."""
        if not MODEL_PATH.exists():
            self.skipTest("Model file not present in this environment.")
        pipeline = _load_pipeline()
        self.assertIsNotNone(pipeline,
                             "_load_pipeline() must return the pipeline when the hash is correct")

    def test_load_pipeline_returns_none_on_hash_mismatch(self):
        """_load_pipeline() must refuse to unpickle a file whose hash doesn't match."""
        if not MODEL_PATH.exists():
            self.skipTest("Model file not present in this environment.")
        with patch('classifier.service.EXPECTED_SHA256', 'deadbeef' * 8):
            result = _load_pipeline()
        self.assertIsNone(result,
                          "_load_pipeline() must return None (not unpickle) when the hash mismatches")

    def test_load_pipeline_logs_error_on_hash_mismatch(self):
        """A hash mismatch must produce an ERROR-level log so it's visible in monitoring."""
        if not MODEL_PATH.exists():
            self.skipTest("Model file not present in this environment.")
        with patch('classifier.service.EXPECTED_SHA256', 'deadbeef' * 8):
            with self.assertLogs('classifier.service', level='ERROR') as cm:
                _load_pipeline()
        error_messages = '\n'.join(cm.output)
        self.assertIn('integrity check', error_messages,
                      "Error log must mention 'integrity check'")
        self.assertIn('EXPECTED_SHA256', error_messages,
                      "Error log must tell the operator what constant to update")

    def test_load_pipeline_returns_none_when_file_is_missing(self):
        """If the model file doesn't exist, _load_pipeline() must return None cleanly."""
        with patch('classifier.service.MODEL_PATH', Path('/nonexistent/model.pkl')):
            result = _load_pipeline()
        self.assertIsNone(result)

    def test_load_pipeline_is_idempotent_with_correct_hash(self):
        """Calling _load_pipeline() twice returns the same cached object."""
        if not MODEL_PATH.exists():
            self.skipTest("Model file not present in this environment.")
        first  = _load_pipeline()
        second = _load_pipeline()
        self.assertIs(first, second,
                      "_load_pipeline() must cache the result and not re-read the file")

    def test_tampered_file_is_rejected(self):
        """
        A file with the correct name but wrong bytes (simulating tampering)
        must be rejected. We simulate this by pointing MODEL_PATH at a
        temporary file with different content.
        """
        import tempfile, os
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
            f.write(b'malicious payload')
            tmp_path = Path(f.name)
        try:
            # Pin the EXPECTED_SHA256 to the real model's hash (not the temp file's)
            real_hash = _file_sha256(MODEL_PATH) if MODEL_PATH.exists() else 'a' * 64
            with patch('classifier.service.MODEL_PATH',     tmp_path), \
                 patch('classifier.service.EXPECTED_SHA256', real_hash):
                result = _load_pipeline()
            self.assertIsNone(result,
                              "A file with wrong bytes must be rejected even if the name is correct")
        finally:
            os.unlink(tmp_path)
