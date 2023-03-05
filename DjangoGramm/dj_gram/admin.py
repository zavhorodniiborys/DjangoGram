from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *
from .forms import CustomUserChangeForm, CustomUserCreationForm


class PostAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['email', 'is_superuser']
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password', 'bio')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )

    add_fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register([Profile, Vote, Images])
