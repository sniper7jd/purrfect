"""Account admin."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'name', 'is_staff', 'email_verified', 'id_verified']
    list_filter = ['is_staff', 'is_active', 'email_verified', 'id_verified']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile', {'fields': ('name', 'bio', 'profile_picture', 'location', 'phone_number')}),
        ('Verification', {'fields': ('email_verified', 'phone_verified', 'id_verified', 'response_rate')}),
    )

