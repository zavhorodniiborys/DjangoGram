from django.contrib import admin

from .models import Profile, Post, User, Vote, Images


class PostAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)


admin.site.register(Post, PostAdmin)
admin.site.register([Profile, User, Vote, Images])
