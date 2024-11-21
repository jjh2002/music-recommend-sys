from django.contrib import admin
from user import models
# Register your models here.
admin.site.register(models.UserInfo)
admin.site.register(models.Music)
admin.site.register(models.UserSongCount)
admin.site.register(models.UserMusicCount)
admin.site.register(models.UserSimilarity)
admin.site.register(models.Comment)
admin.site.register(models.MusicSimilarity)
admin.site.register(models.CommentLike)
