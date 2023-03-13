from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *
from .forms import *


class PostAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserAdminCreateForm
    form = CustomUserFillForm
    model = CustomUser
    list_display = ['email', 'is_superuser']
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'first_name', 'last_name', 'avatar', 'password1', 'password2', 'bio')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )

    add_fieldsets = (
        (None, {'fields': ('email',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register([Vote, Images])
