"""
accounts/tests.py
─────────────────
Tests for Finding #1: Privilege escalation via PATCH /api/auth/me/

Before the fix, `UserSerializer` exposed `role`, `is_active`, and `office_id`
as writable fields on the MeView, letting any authenticated user self-promote.
After the fix, those fields are in `read_only_fields` — PATCH requests that
include them are silently ignored.
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from accounts.models import User, Office


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_office(name='Test Office', code='TST'):
    return Office.objects.create(name=name, code=code)

def make_user(username, role=User.Role.FACULTY, office=None, password='securepass123!'):
    u = User.objects.create_user(username=username, password=password, role=role)
    if office:
        u.office = office
        u.save()
    return u


# ── Tests ─────────────────────────────────────────────────────────────────────

class MeViewPrivilegeEscalationTests(APITestCase):
    """
    PATCH /api/auth/me/ must not allow a user to write privilege-gated fields.
    """

    def setUp(self):
        self.office_a = make_office('Dept A', 'DPTA')
        self.office_b = make_office('Dept B', 'DPTB')
        self.faculty  = make_user('faculty_user', role=User.Role.FACULTY, office=self.office_a)
        self.client.force_authenticate(user=self.faculty)

    # ── role escalation ───────────────────────────────────────────────────────

    def test_faculty_cannot_self_promote_to_superadmin(self):
        resp = self.client.patch('/api/auth/me/', {'role': 'superadmin'}, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        self.faculty.refresh_from_db()
        self.assertEqual(self.faculty.role, User.Role.FACULTY,
                         "role must remain 'faculty' after a self-promote attempt")

    def test_faculty_cannot_self_promote_to_records_officer(self):
        resp = self.client.patch('/api/auth/me/', {'role': 'records_officer'}, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        self.faculty.refresh_from_db()
        self.assertEqual(self.faculty.role, User.Role.FACULTY)

    def test_faculty_cannot_self_promote_to_program_chair(self):
        resp = self.client.patch('/api/auth/me/', {'role': 'program_chair'}, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        self.faculty.refresh_from_db()
        self.assertEqual(self.faculty.role, User.Role.FACULTY)

    # ── is_active ─────────────────────────────────────────────────────────────

    def test_faculty_cannot_self_deactivate(self):
        resp = self.client.patch('/api/auth/me/', {'is_active': False}, format='json')
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        self.faculty.refresh_from_db()
        self.assertTrue(self.faculty.is_active,
                        "is_active must not be writable via /api/auth/me/")

    def test_faculty_cannot_self_activate_a_deactivated_account(self):
        self.faculty.is_active = False
        self.faculty.save()
        self.client.patch('/api/auth/me/', {'is_active': True}, format='json')
        self.faculty.refresh_from_db()
        self.assertFalse(self.faculty.is_active,
                         "is_active must not be writable via /api/auth/me/")

    # ── office_id must not appear in the writable field set ───────────────────

    def test_office_reassignment_ignored_on_me_endpoint(self):
        """
        office_id was removed from UserSerializer.fields entirely — the endpoint
        must ignore it rather than reassigning the user's office.
        """
        original_office_id = self.faculty.office_id
        self.client.patch('/api/auth/me/', {'office_id': self.office_b.pk}, format='json')
        self.faculty.refresh_from_db()
        self.assertEqual(self.faculty.office_id, original_office_id,
                         "office_id must not be reassignable via /api/auth/me/")

    # ── permitted edits still work ────────────────────────────────────────────

    def test_faculty_can_update_phone(self):
        resp = self.client.patch('/api/auth/me/', {'phone': '+639001234567'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.faculty.refresh_from_db()
        self.assertEqual(self.faculty.phone, '+639001234567')

    def test_faculty_can_update_display_name(self):
        resp = self.client.patch(
            '/api/auth/me/',
            {'first_name': 'Maria', 'last_name': 'Santos'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.faculty.refresh_from_db()
        self.assertEqual(self.faculty.first_name, 'Maria')
        self.assertEqual(self.faculty.last_name, 'Santos')

    # ── combined escalation attempt ───────────────────────────────────────────

    def test_combined_escalation_payload_all_ignored(self):
        """
        A single PATCH that bundles role + is_active + office_id + a
        legitimate field must silently drop the privilege fields while
        still applying the legitimate one.
        """
        resp = self.client.patch(
            '/api/auth/me/',
            {
                'role':      'superadmin',
                'is_active': False,
                'office_id': self.office_b.pk,
                'phone':     '+639009876543',
            },
            format='json',
        )
        self.assertIn(resp.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        self.faculty.refresh_from_db()
        self.assertEqual(self.faculty.role,      User.Role.FACULTY,  "role unchanged")
        self.assertTrue(self.faculty.is_active,                       "is_active unchanged")
        self.assertEqual(self.faculty.office_id, self.office_a.pk,    "office unchanged")

    # ── unauthenticated requests ──────────────────────────────────────────────

    def test_unauthenticated_me_returns_401(self):
        anon_client = APIClient()
        resp = anon_client.patch('/api/auth/me/', {'role': 'superadmin'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
