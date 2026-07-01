"""
tracking/tests.py
─────────────────
Tests for Finding #2 (tracking consumer slice): consumers.check_access.

Before the fix, check_access only excluded RESTRICTED documents for non-admins
— it let any authenticated user subscribe to the WebSocket feed of any
PUBLIC/INTERNAL/CONFIDENTIAL document regardless of ownership or office.

After the fix, check_access is:

    return Document.objects.visible_to(user).filter(
        tracking_number=tracking_number
    ).exists()

Since check_access is a thin, transparent wrapper around DocumentQuerySet
(which is fully tested in documents/tests.py), these tests focus on:

  1. The integration wiring — that check_access correctly delegates to
     visible_to() and not to a hand-rolled confidentiality check.
  2. Key boundary cases specific to the tracking-number lookup path (e.g.
     a tracking number that doesn't exist at all must return False).

For async execution: check_access is decorated with @database_sync_to_async,
so we call it through asgiref's async_to_sync() adapter.
"""
from django.test import TestCase
from asgiref.sync import async_to_sync

from accounts.models import User, Office
from documents.models import Document, DocumentType
from tracking.consumers import DocumentTrackingConsumer


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_office(name, code):
    return Office.objects.create(name=name, code=code)

def make_user(username, role=User.Role.FACULTY, office=None, pw='securepass123!'):
    u = User.objects.create_user(username=username, password=pw, role=role)
    if office:
        u.office = office
        u.save()
    return u

def make_doc_type():
    dt, _ = DocumentType.objects.get_or_create(
        name='Tracking Test Type', defaults={'code': 'TRK'}
    )
    return dt

def make_doc(submitted_by, current_office=None,
             confidentiality=Document.Confidentiality.INTERNAL):
    return Document.objects.create(
        title='Tracking Test Doc',
        doc_type=make_doc_type(),
        submitted_by=submitted_by,
        current_office=current_office,
        confidentiality=confidentiality,
        file='test/tracking.pdf',
    )

def check_access(user, tracking_number):
    """Synchronous wrapper around the async check_access consumer method."""
    consumer = DocumentTrackingConsumer()
    return async_to_sync(consumer.check_access)(user, tracking_number)


# ── Tests ─────────────────────────────────────────────────────────────────────

class ConsumerCheckAccessTests(TestCase):
    """
    consumers.check_access must enforce the same policy as visible_to().
    """

    def setUp(self):
        self.dept_a = make_office('WS Dept A', 'WSA')
        self.dept_b = make_office('WS Dept B', 'WSB')

        self.admin   = make_user('ws_admin',   role=User.Role.RECORDS_OFFICER)
        self.chair_a = make_user('ws_chair_a', role=User.Role.PROGRAM_CHAIR, office=self.dept_a)
        self.fac_a   = make_user('ws_fac_a',   role=User.Role.FACULTY,       office=self.dept_a)
        self.fac_b   = make_user('ws_fac_b',   role=User.Role.FACULTY,       office=self.dept_b)

        self.own_doc        = make_doc(self.fac_a, self.dept_a, Document.Confidentiality.PUBLIC)
        self.others_doc     = make_doc(self.fac_b, self.dept_b, Document.Confidentiality.PUBLIC)
        self.restricted_doc = make_doc(self.admin, self.dept_a, Document.Confidentiality.RESTRICTED)

    # ── faculty ───────────────────────────────────────────────────────────────

    def test_faculty_can_access_own_doc_feed(self):
        self.assertTrue(
            check_access(self.fac_a, self.own_doc.tracking_number),
            "faculty must be able to subscribe to their own document's WS feed"
        )

    def test_faculty_cannot_access_other_faculty_doc_feed(self):
        self.assertFalse(
            check_access(self.fac_a, self.others_doc.tracking_number),
            "faculty must NOT be able to subscribe to another user's WS feed"
        )

    def test_faculty_cannot_access_restricted_doc_feed(self):
        self.assertFalse(
            check_access(self.fac_a, self.restricted_doc.tracking_number),
            "faculty must NOT be able to subscribe to a RESTRICTED doc's WS feed"
        )

    # ── records_admin ─────────────────────────────────────────────────────────

    def test_records_admin_can_access_restricted_doc_feed(self):
        self.assertTrue(
            check_access(self.admin, self.restricted_doc.tracking_number),
            "records_admin must be able to subscribe to RESTRICTED docs"
        )

    def test_records_admin_can_access_any_doc_feed(self):
        for doc in (self.own_doc, self.others_doc, self.restricted_doc):
            with self.subTest(tracking_number=doc.tracking_number):
                self.assertTrue(check_access(self.admin, doc.tracking_number))

    # ── program_chair ─────────────────────────────────────────────────────────

    def test_program_chair_can_access_doc_in_their_office(self):
        # own_doc.current_office = dept_a = chair_a's office
        self.assertTrue(
            check_access(self.chair_a, self.own_doc.tracking_number),
            "program_chair must be able to subscribe to docs in their office"
        )

    def test_program_chair_cannot_access_doc_in_other_office(self):
        # others_doc.current_office = dept_b ≠ chair_a's office
        self.assertFalse(
            check_access(self.chair_a, self.others_doc.tracking_number),
            "program_chair must NOT subscribe to docs outside their office"
        )

    # ── non-existent tracking number ──────────────────────────────────────────

    def test_nonexistent_tracking_number_returns_false(self):
        self.assertFalse(
            check_access(self.fac_a, 'ASC-000000-ZZZZZZ'),
            "a tracking number that doesn't exist must return False, not raise"
        )

    def test_nonexistent_tracking_number_returns_false_for_admin(self):
        self.assertFalse(
            check_access(self.admin, 'ASC-000000-ZZZZZZ'),
            "even admins must get False for a non-existent tracking number"
        )
