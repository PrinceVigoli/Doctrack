from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Office

@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active']

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ['username', 'get_full_name', 'role', 'office', 'is_active']
    list_filter   = ['role', 'office', 'is_active']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('ASC Info', {'fields': ('role', 'office', 'phone', 'avatar')}),
    )
