"""
config/tests.py
───────────────
Tests for Finding #4: insecure settings defaults.

Before the fix, settings.py silently fell back to 'change-me-in-production'
for SECRET_KEY and True for DEBUG when those env vars weren't set — the
server started in an insecure state without any indication of the problem.

After the fix, _resolve_security_settings() raises ImproperlyConfigured on
unsafe combinations in non-development environments, and returns safe defaults
in development so existing local workflows are unaffected.

The validation logic lives in _resolve_security_settings() (a pure function)
so it can be tested directly without reloading the entire settings module.
"""
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from config.settings import _resolve_security_settings


class SettingsValidationProductionTests(SimpleTestCase):
    """
    In any DJANGO_ENV other than 'development', insecure combinations must
    raise ImproperlyConfigured and prevent the server from starting.
    """

    # ── SECRET_KEY ────────────────────────────────────────────────────────────

    def test_raises_when_secret_key_is_unset_in_production(self):
        with self.assertRaises(ImproperlyConfigured) as cm:
            _resolve_security_settings('production', None, 'False')
        self.assertIn('SECRET_KEY', str(cm.exception))

    def test_raises_when_secret_key_is_empty_string_in_production(self):
        with self.assertRaises(ImproperlyConfigured):
            _resolve_security_settings('production', '', 'False')

    def test_raises_when_secret_key_is_unset_in_staging(self):
        """Any DJANGO_ENV value that isn't 'development' is treated as production."""
        with self.assertRaises(ImproperlyConfigured):
            _resolve_security_settings('staging', None, 'False')

    def test_raises_when_secret_key_is_unset_in_unknown_env(self):
        with self.assertRaises(ImproperlyConfigured):
            _resolve_security_settings('unknown', None, 'False')

    # ── DEBUG ────────────────────────────────────────────────────────────────

    def test_raises_when_debug_is_true_in_production(self):
        with self.assertRaises(ImproperlyConfigured) as cm:
            _resolve_security_settings('production', 'real-secret-key-here', 'True')
        self.assertIn('DEBUG', str(cm.exception))

    def test_raises_when_debug_is_true_in_staging(self):
        with self.assertRaises(ImproperlyConfigured):
            _resolve_security_settings('staging', 'real-secret-key-here', 'True')

    # ── valid production configuration ────────────────────────────────────────

    def test_valid_production_config_returns_correctly(self):
        key, debug = _resolve_security_settings('production', 'a-real-secret', 'False')
        self.assertEqual(key, 'a-real-secret')
        self.assertFalse(debug)

    def test_valid_staging_config_returns_correctly(self):
        key, debug = _resolve_security_settings('staging', 'a-real-secret', 'False')
        self.assertEqual(key, 'a-real-secret')
        self.assertFalse(debug)

    def test_debug_unset_in_production_defaults_to_false(self):
        """When DEBUG env var is not set at all, it must default to False in production."""
        key, debug = _resolve_security_settings('production', 'a-real-secret', None)
        self.assertFalse(debug,
                         "Unset DEBUG must default to False outside development, not True")

    def test_debug_false_explicit_in_production_is_accepted(self):
        key, debug = _resolve_security_settings('production', 'a-real-secret', 'False')
        self.assertFalse(debug)


class SettingsValidationDevelopmentTests(SimpleTestCase):
    """
    In 'development', the insecure-default fallbacks must still work so that
    local `cp .env.example .env; python manage.py runserver` keeps working.
    """

    def test_missing_secret_key_in_development_uses_insecure_fallback(self):
        """Missing SECRET_KEY in dev must not raise — it returns the insecure dev fallback."""
        key, debug = _resolve_security_settings('development', None, None)
        self.assertIn('insecure', key,
                      "Dev fallback SECRET_KEY must contain 'insecure' so it's obviously wrong in logs")

    def test_empty_secret_key_in_development_uses_insecure_fallback(self):
        key, _ = _resolve_security_settings('development', '', None)
        self.assertIn('insecure', key)

    def test_debug_unset_in_development_defaults_to_true(self):
        """When DEBUG env var is not set, it should default to True in development."""
        _, debug = _resolve_security_settings('development', 'any-key', None)
        self.assertTrue(debug,
                        "Unset DEBUG must default to True in development for DX convenience")

    def test_debug_false_explicit_in_development_is_respected(self):
        """Developers can opt into DEBUG=False locally (e.g. to test production behaviour)."""
        _, debug = _resolve_security_settings('development', 'any-key', 'False')
        self.assertFalse(debug)

    def test_debug_true_explicit_in_development_is_accepted(self):
        _, debug = _resolve_security_settings('development', 'any-key', 'True')
        self.assertTrue(debug)

    def test_real_secret_key_in_development_is_used_as_is(self):
        """If a developer has set a real SECRET_KEY locally, it must be used unchanged."""
        key, _ = _resolve_security_settings('development', 'a-real-secret', None)
        self.assertEqual(key, 'a-real-secret')


class SettingsValidationReturnTypeTests(SimpleTestCase):
    """Verify the return type contract: always (str, bool)."""

    def test_returns_str_and_bool_in_development(self):
        key, debug = _resolve_security_settings('development', None, None)
        self.assertIsInstance(key,   str)
        self.assertIsInstance(debug, bool)

    def test_returns_str_and_bool_in_production(self):
        key, debug = _resolve_security_settings('production', 'secret', 'False')
        self.assertIsInstance(key,   str)
        self.assertIsInstance(debug, bool)

    def test_debug_string_false_produces_bool_false(self):
        _, debug = _resolve_security_settings('development', 'k', 'False')
        self.assertIs(debug, False)
        self.assertIsInstance(debug, bool)

    def test_debug_string_true_produces_bool_true(self):
        _, debug = _resolve_security_settings('development', 'k', 'True')
        self.assertIs(debug, True)
        self.assertIsInstance(debug, bool)
