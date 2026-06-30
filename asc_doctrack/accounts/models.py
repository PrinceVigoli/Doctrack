from django.contrib.auth.models import AbstractUser
from django.db import models


class Office(models.Model):
    name        = models.CharField(max_length=150, unique=True)
    code        = models.CharField(max_length=20,  unique=True)
    description = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    is_records_office = models.BooleanField(
        default=False,
        help_text="Mark this if this is the Records Office."
    )
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.code} – {self.name}"


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERADMIN     = 'superadmin',     'Super Admin'
        RECORDS_OFFICER= 'records_officer','Records Officer'
        PROGRAM_CHAIR  = 'program_chair',  'Program Chair'
        FACULTY        = 'faculty',        'Faculty'

    role   = models.CharField(max_length=20, choices=Role.choices, default=Role.FACULTY)
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='members')
    phone  = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN or self.is_superuser

    @property
    def is_records_admin(self):
        """Backwards-compat: records officer or above can manage documents."""
        return self.role in (self.Role.SUPERADMIN, self.Role.RECORDS_OFFICER) or self.is_superuser

    @property
    def is_program_chair(self):
        return self.role == self.Role.PROGRAM_CHAIR

    @property
    def is_faculty(self):
        return self.role == self.Role.FACULTY

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
