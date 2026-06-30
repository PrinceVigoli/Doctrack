"""
Run once to seed offices/departments and set up the superadmin.
  cd asc_doctrack
  python ../seed.py
"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from accounts.models import Office, User

# ── Offices / Departments ─────────────────────────────────────────────────────
OFFICES = [
    # Administrative offices
    dict(code='OP',  name='Office of the President',             is_records_office=False, description='Office of the College President'),
    dict(code='RO',  name='Records Office',                      is_records_office=True,  description='Manages official college records and documents'),
    dict(code='REG', name='Registrar',                           is_records_office=False, description='Student registration and academic records'),
    dict(code='FIN', name='Finance Office',                      is_records_office=False, description='Budget, accounting, and financial management'),
    dict(code='HR',  name='Human Resources',                     is_records_office=False, description='Personnel and human resource management'),
    dict(code='OSA', name='Office of Student Affairs',           is_records_office=False, description='Student welfare, activities, and services'),
    dict(code='GSO', name='General Services Office',             is_records_office=False, description='Facilities, maintenance, and logistics'),
    dict(code='LIB', name='Library',                             is_records_office=False, description='College library and learning resources'),
    dict(code='RDE', name='Research & Development Extension',    is_records_office=False, description='Research, development, and extension programs'),
    dict(code='ICT', name='ICT Office',                          is_records_office=False, description='Information and communications technology'),
    # Academic departments
    dict(code='CTE', name='College of Teacher Education',        is_records_office=False, description='Education and teacher training programs'),
    dict(code='CIT', name='College of Information Technology',   is_records_office=False, description='IT and computer science programs'),
    dict(code='CAS', name='College of Arts and Sciences',        is_records_office=False, description='Liberal arts and sciences programs'),
    dict(code='CBA', name='College of Business Administration',  is_records_office=False, description='Business and management programs'),
    dict(code='CA',  name='College of Agriculture',              is_records_office=False, description='Agriculture and related programs'),
    dict(code='CET', name='College of Engineering & Technology', is_records_office=False, description='Engineering and technology programs'),
    dict(code='CN',  name='College of Nursing',                  is_records_office=False, description='Nursing and health science programs'),
]

print("\n── Seeding offices ──────────────────────────────────────────")
for o in OFFICES:
    obj, created = Office.objects.get_or_create(
        code=o['code'],
        defaults=dict(name=o['name'], description=o['description'],
                      is_records_office=o['is_records_office'], is_active=True)
    )
    print(f"  {'✔ Created' if created else '– Exists '} {o['code']:5} {o['name']}")

# ── Superadmin user ───────────────────────────────────────────────────────────
print("\n── Seeding superadmin ───────────────────────────────────────")
admin, created = User.objects.get_or_create(
    username='admin',
    defaults=dict(
        first_name='Super', last_name='Admin',
        email='admin@asc.edu.ph',
        role=User.Role.SUPERADMIN,
        is_staff=True, is_superuser=True,
    )
)
if created:
    admin.set_password('Admin@1234')
admin.role = User.Role.SUPERADMIN
admin.office = Office.objects.get(code='RO')
admin.save()
print(f"  {'✔ Created' if created else '✔ Updated'} admin → SuperAdmin @ Records Office")

print("\n✅ Seed complete.\n")
