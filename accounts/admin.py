from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from accounts.models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "department", "support_level", "is_active")
    list_filter = ("role", "support_level", "department", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Nexus Desk", {"fields": ("role", "department", "support_level")}),
    )
