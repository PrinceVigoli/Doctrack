"""
documents/tests.py
──────────────────
Tests for Finding #2: Broken access control — non-admins can view all docs.

Before the fix, `get_queryset`, `get_object`, `DocumentQRView`, and
`consumers.check_access` all only excluded RESTRICTED documents for
non-admins, but never filtered by ownership or office.  Any faculty
user could list, retrieve, and watch every PUBLIC/INTERNAL/CONFIDENTIAL
document in the system.

After the fix, Document.objects.visible_to() enforces:
  - records_admin    → all documents, including RESTRICTED
  - program_chair    → own submissions + docs currently in their office (except RESTRICTED)
  - faculty          → own submissions only (except RESTRICTED)

All three call sites now delegate exclusively to visible_to(), so these
tests cover the queryset method in depth and smoke-test each call site.
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, Office
from documents.models import Document, DocumentType


# ── Shared fixtures ───────────────────────────────────────────────────────────

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
        name='Test Type', defaults={'code': 'TST'}
    )
    return dt

def make_doc(submitted_by, current_office=None,
             confidentiality=Document.Confidentiality.INTERNAL,
             title='Test Doc'):
    """
    Creates a Document, bypassing file-upload validation (the FileField
    stores a path string; for queryset/access tests no actual file is needed).
    """
    return Document.objects.create(
        title=title,
        doc_type=make_doc_type(),
        submitted_by=submitted_by,
        current_office=current_office,
        confidentiality=confidentiality,
        file='test/placeholder.pdf',
    )


# ── DocumentQuerySet.visible_to() unit tests ──────────────────────────────────

class DocumentQuerySetVisibleToTests(TestCase):
    """
    Direct unit tests on DocumentQuerySet.visible_to().
    These are the ground-truth correctness tests; if these pass the view and
    consumer tests below are testing integration plumbing only.
    """

    def setUp(self):
        self.records_office = make_office('Records Office', 'REC')
        self.dept_a         = make_office('Department A',   'DPTA')
        self.dept_b         = make_office('Department B',   'DPTB')

        self.admin   = make_user('admin',   role=User.Role.RECORDS_OFFICER, office=self.records_office)
        self.chair_a = make_user('chair_a', role=User.Role.PROGRAM_CHAIR,   office=self.dept_a)
        self.chair_b = make_user('chair_b', role=User.Role.PROGRAM_CHAIR,   office=self.dept_b)
        self.fac_a   = make_user('fac_a',   role=User.Role.FACULTY,         office=self.dept_a)
        self.fac_b   = make_user('fac_b',   role=User.Role.FACULTY,         office=self.dept_b)

        # Docs by fac_a, currently sitting in dept_a or dept_b
        self.doc_pub_fac_a_dept_a  = make_doc(self.fac_a, self.dept_a, Document.Confidentiality.PUBLIC,    'Public fac_a dept_a')
        self.doc_int_fac_a_dept_b  = make_doc(self.fac_a, self.dept_b, Document.Confidentiality.INTERNAL,  'Internal fac_a dept_b')
        # Doc by fac_b, in dept_b
        self.doc_pub_fac_b_dept_b  = make_doc(self.fac_b, self.dept_b, Document.Confidentiality.PUBLIC,    'Public fac_b dept_b')
        # Restricted doc by admin
        self.doc_restricted        = make_doc(self.admin, self.dept_a, Document.Confidentiality.RESTRICTED, 'Restricted admin')

    # ── records_admin ─────────────────────────────────────────────────────────

    def test_records_admin_sees_all_docs_including_restricted(self):
        qs = Document.objects.visible_to(self.admin)
        self.assertIn(self.doc_pub_fac_a_dept_a, qs)
        self.assertIn(self.doc_int_fac_a_dept_b, qs)
        self.assertIn(self.doc_pub_fac_b_dept_b, qs)
        self.assertIn(self.doc_restricted,        qs)
        self.assertEqual(qs.count(), 4)

    # ── faculty ───────────────────────────────────────────────────────────────

    def test_faculty_sees_only_own_submissions(self):
        qs = Document.objects.visible_to(self.fac_a)
        # fac_a submitted two docs
        self.assertIn(self.doc_pub_fac_a_dept_a, qs)
        self.assertIn(self.doc_int_fac_a_dept_b, qs)
        # fac_a did NOT submit these
        self.assertNotIn(self.doc_pub_fac_b_dept_b, qs,
                         "faculty must not see docs they did not submit")
        self.assertNotIn(self.doc_restricted, qs)

    def test_faculty_cannot_see_restricted_even_if_currently_in_their_office(self):
        """RESTRICTED is admin-only regardless of where the doc currently sits."""
        # doc_restricted.current_office = dept_a, same as fac_a — still invisible
        qs = Document.objects.visible_to(self.fac_a)
        self.assertNotIn(self.doc_restricted, qs)

    def test_faculty_cannot_see_other_faculty_docs_by_office_proximity(self):
        """Being in the same department office must not grant visibility of others' docs."""
        # fac_a and chair_a are both in dept_a; doc_pub_fac_b_dept_b is in dept_b.
        # fac_b submitted doc_pub_fac_b_dept_b — fac_a must not see it.
        qs = Document.objects.visible_to(self.fac_a)
        self.assertNotIn(self.doc_pub_fac_b_dept_b, qs)

    def test_faculty_without_own_docs_sees_empty_queryset(self):
        newcomer = make_user('newcomer', role=User.Role.FACULTY, office=self.dept_a)
        qs = Document.objects.visible_to(newcomer)
        self.assertEqual(qs.count(), 0)

    # ── program_chair ─────────────────────────────────────────────────────────

    def test_program_chair_sees_own_submissions(self):
        chair_doc = make_doc(self.chair_a, self.dept_b, Document.Confidentiality.PUBLIC,
                             'Chair A own doc')
        qs = Document.objects.visible_to(self.chair_a)
        self.assertIn(chair_doc, qs,
                      "program_chair must see their own submissions")

    def test_program_chair_sees_docs_currently_in_their_office(self):
        qs = Document.objects.visible_to(self.chair_a)
        # doc_pub_fac_a_dept_a is in dept_a — chair_a's office
        self.assertIn(self.doc_pub_fac_a_dept_a, qs,
                      "program_chair must see docs currently in their office")

    def test_program_chair_cannot_see_docs_in_other_office(self):
        qs = Document.objects.visible_to(self.chair_a)
        # doc_pub_fac_b_dept_b is in dept_b — chair_a's is dept_a
        self.assertNotIn(self.doc_pub_fac_b_dept_b, qs,
                         "program_chair must not see docs in a different office")

    def test_program_chair_cannot_see_restricted_even_in_their_office(self):
        # doc_restricted.current_office = dept_a — same as chair_a, still invisible
        qs = Document.objects.visible_to(self.chair_a)
        self.assertNotIn(self.doc_restricted, qs)

    def test_program_chair_without_office_sees_only_own_submissions(self):
        """A program_chair with no office assigned falls back to own-submissions only."""
        chair_no_office = make_user('chair_no_office', role=User.Role.PROGRAM_CHAIR)
        own_doc = make_doc(chair_no_office, self.dept_a)
        qs = Document.objects.visible_to(chair_no_office)
        self.assertIn(own_doc, qs)
        self.assertNotIn(self.doc_pub_fac_a_dept_a, qs,
                         "program_chair with no office must not see dept docs")

    # ── cross-cutting: RESTRICTED always excluded for non-admins ──────────────

    def test_restricted_always_excluded_for_non_admins(self):
        for user in (self.chair_a, self.chair_b, self.fac_a, self.fac_b):
            with self.subTest(user=user.username):
                qs = Document.objects.visible_to(user)
                self.assertNotIn(self.doc_restricted, qs)


# ── Document.is_visible_to property tests ────────────────────────────────────

class DocumentIsVisibleToPropertyTests(TestCase):
    """
    is_visible_to is a property returning a callable — it now delegates to
    Document.objects.visible_to() rather than re-implementing the check.
    """

    def setUp(self):
        self.records_office = make_office('Records', 'REC')
        self.dept           = make_office('Dept',    'DPT')
        self.admin   = make_user('admin2',   role=User.Role.RECORDS_OFFICER)
        self.faculty = make_user('faculty2', role=User.Role.FACULTY)
        self.other   = make_user('other2',   role=User.Role.FACULTY)

    def test_admin_can_see_restricted_doc(self):
        doc = make_doc(self.admin, confidentiality=Document.Confidentiality.RESTRICTED)
        self.assertTrue(doc.is_visible_to(self.admin))

    def test_faculty_can_see_own_non_restricted_doc(self):
        doc = make_doc(self.faculty, confidentiality=Document.Confidentiality.INTERNAL)
        self.assertTrue(doc.is_visible_to(self.faculty))

    def test_faculty_cannot_see_someone_elses_doc(self):
        doc = make_doc(self.admin, confidentiality=Document.Confidentiality.PUBLIC)
        self.assertFalse(doc.is_visible_to(self.faculty))


# ── DocumentViewSet HTTP-level access tests ───────────────────────────────────

class DocumentViewSetAccessTests(APITestCase):
    """
    Smoke-tests that the HTTP layer (list, retrieve) enforces visible_to().
    Detailed policy coverage is in DocumentQuerySetVisibleToTests.
    """

    def setUp(self):
        self.dept_a = make_office('Dept A', 'A')
        self.dept_b = make_office('Dept B', 'B')
        self.admin   = make_user('vset_admin',   role=User.Role.RECORDS_OFFICER)
        self.fac_a   = make_user('vset_fac_a',   role=User.Role.FACULTY, office=self.dept_a)
        self.fac_b   = make_user('vset_fac_b',   role=User.Role.FACULTY, office=self.dept_b)

        self.own_doc       = make_doc(self.fac_a, self.dept_a, Document.Confidentiality.PUBLIC,
                                     'fac_a own')
        self.others_doc    = make_doc(self.fac_b, self.dept_b, Document.Confidentiality.PUBLIC,
                                     'fac_b own')
        self.restricted_doc = make_doc(self.admin, self.dept_a, Document.Confidentiality.RESTRICTED,
                                      'restricted')

    # ── list ──────────────────────────────────────────────────────────────────

    def test_faculty_list_contains_only_own_docs(self):
        self.client.force_authenticate(user=self.fac_a)
        resp = self.client.get('/api/docs/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [d['id'] for d in resp.data.get('results', resp.data)]
        self.assertIn(self.own_doc.pk,       ids, "own doc must be in list")
        self.assertNotIn(self.others_doc.pk, ids, "other faculty's doc must NOT be in list")
        self.assertNotIn(self.restricted_doc.pk, ids, "RESTRICTED must NOT be in list")

    def test_records_officer_list_contains_all_docs(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get('/api/docs/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = [d['id'] for d in resp.data.get('results', resp.data)]
        for doc in (self.own_doc, self.others_doc, self.restricted_doc):
            self.assertIn(doc.pk, ids)

    # ── retrieve ──────────────────────────────────────────────────────────────

    def test_faculty_retrieve_own_doc_returns_200(self):
        self.client.force_authenticate(user=self.fac_a)
        resp = self.client.get(f'/api/docs/{self.own_doc.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_faculty_retrieve_other_faculty_doc_returns_404(self):
        self.client.force_authenticate(user=self.fac_a)
        resp = self.client.get(f'/api/docs/{self.others_doc.pk}/')
        # 404 (not 403) because get_queryset scopes the queryset — DRF raises
        # Http404 via get_object_or_404 when the pk isn't in the queryset.
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND,
                         "faculty must get 404 (not 403) for another user's document")

    def test_faculty_retrieve_restricted_doc_returns_404(self):
        self.client.force_authenticate(user=self.fac_a)
        resp = self.client.get(f'/api/docs/{self.restricted_doc.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_records_officer_retrieve_restricted_doc_returns_200(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(f'/api/docs/{self.restricted_doc.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_unauthenticated_retrieve_returns_401(self):
        resp = self.client.get(f'/api/docs/{self.own_doc.pk}/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ── DocumentQRView HTTP-level access tests ────────────────────────────────────

class DocumentQRViewAccessTests(APITestCase):
    """
    The QR endpoint now returns 404 (not 403) for out-of-scope documents —
    scanning an opaque QR code must not even confirm the document exists.
    """

    def setUp(self):
        self.dept_a = make_office('QR Dept A', 'QRA')
        self.dept_b = make_office('QR Dept B', 'QRB')
        self.admin   = make_user('qr_admin',   role=User.Role.RECORDS_OFFICER)
        self.fac_a   = make_user('qr_fac_a',   role=User.Role.FACULTY, office=self.dept_a)
        self.fac_b   = make_user('qr_fac_b',   role=User.Role.FACULTY, office=self.dept_b)

        self.own_doc        = make_doc(self.fac_a, self.dept_a, Document.Confidentiality.PUBLIC)
        self.others_doc     = make_doc(self.fac_b, self.dept_b, Document.Confidentiality.PUBLIC)
        self.restricted_doc = make_doc(self.admin, self.dept_a, Document.Confidentiality.RESTRICTED)

    def test_faculty_qr_own_doc_succeeds(self):
        self.client.force_authenticate(user=self.fac_a)
        resp = self.client.get(f'/api/docs/{self.own_doc.pk}/qr/')
        self.assertNotEqual(resp.status_code, status.HTTP_404_NOT_FOUND,
                            "faculty must be able to QR-scan their own doc")

    def test_faculty_qr_other_faculty_doc_returns_404(self):
        self.client.force_authenticate(user=self.fac_a)
        resp = self.client.get(f'/api/docs/{self.others_doc.pk}/qr/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND,
                         "scanning another faculty's doc must return 404, not 403")

    def test_faculty_qr_restricted_doc_returns_404(self):
        self.client.force_authenticate(user=self.fac_a)
        resp = self.client.get(f'/api/docs/{self.restricted_doc.pk}/qr/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND,
                         "scanning a RESTRICTED doc must return 404, not 403")

    def test_records_officer_qr_restricted_doc_succeeds(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(f'/api/docs/{self.restricted_doc.pk}/qr/')
        self.assertNotEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_qr_returns_401(self):
        resp = self.client.get(f'/api/docs/{self.own_doc.pk}/qr/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
