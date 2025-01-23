from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


class CustomUserAdmin(UserAdmin):
    model = User

    list_display = (
        'username',
        'email',
        'is_active',
        'is_superuser',
        'is_admin',
        'joined_at',
        'updated_at',
        'last_login',
    )

    prepopulated_fields = {'slug': ('username', 'email')}

    list_filter = ('is_active', 'is_superuser', 'is_admin', 'joined_at')

    search_fields = ('username', 'email')

    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (_('Personal Info'), {'fields': ('avatar', 'slug', 'skill_rating')}),
        (_('Permissions'), {'fields': ('is_active', 'is_admin', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'joined_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active', 'is_admin', 'is_superuser'),
        }),
    )

    def save_model(self, request, obj, form, change):
        self._ensure_slug(obj)
        self._handle_error(obj)
        super().save_model(request, obj, form, change)

    def _ensure_slug(self, obj):
        if not obj.slug:
            obj.slug = obj.username  # Or any other logic to generate the slug
        if not obj.slug.strip():
            raise ValueError("Slug cannot be empty.")

    def _handle_error(self, obj):
        if not obj.email or not obj.username:
            raise ValueError("Both email and username must be provided.")
        if '@' not in obj.email:
            raise ValueError("Invalid email format.")

    def _validate_user_permissions(self, obj):
        if obj.is_superuser and not obj.is_admin:
            raise ValueError("Superuser must be an admin.")
        return obj


admin.site.register(User, CustomUserAdmin)