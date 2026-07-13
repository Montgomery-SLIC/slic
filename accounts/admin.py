from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, ResearcherInvitation


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'name', 'institution', 'admin', 'is_active', 'date_joined')
    list_filter = ('admin', 'is_active', 'funded', 'mailing_list')
    search_fields = ('email_bidx',)
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email_bidx', 'password')}),
        ('Profile', {'fields': ('name_ciphertext', 'institution_ciphertext', 'country_ciphertext', 'faculty_ciphertext', 'research_level_ciphertext', 'funded', 'mailing_list')}),
        ('Permissions', {'fields': ('admin', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Account state', {'fields': ('failed_attempts', 'locked_at', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email_bidx', 'password1', 'password2'),
        }),
    )
    readonly_fields = ('date_joined',)

    def email(self, obj):
        return obj.email

    def name(self, obj):
        return obj.name

    def institution(self, obj):
        return obj.institution


@admin.register(ResearcherInvitation)
class ResearcherInvitationAdmin(admin.ModelAdmin):
    list_display = ('registration_code', 'used', 'user', 'created_at')
    list_filter = ('used',)
    ordering = ('-created_at',)
