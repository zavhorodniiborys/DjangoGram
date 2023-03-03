from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *
from .forms import CustomUserChangeForm, CustomUserCreationForm


class PostAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)

class CustomUserAdmin(UserAdmin):
    # add_form = CustomUserCreationForm
    # form = CustomUserChangeForm
    model = BUser
    list_display = ['username', 'email', 'is_superuser']

    fieldsets = UserAdmin.fieldsets


admin.site.register(BUser, CustomUserAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register([Profile, User, Vote, Images])
