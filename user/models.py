from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


# Create your models here.
# 存储用户信息
class UserInfo(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=20)
    phone = models.CharField(max_length=11)


# 新建数据 c   python manage.py migrate
# UserInfo.objects.create(username='root', password='123', phone='12345678901')
# 音乐信息，包括其种类，名称，演唱者，播放次数，url
class Music(models.Model):
    CATEGORY_CHOICES = [
        ('pop', '流行'),
        ('rock', '摇滚'),
        ('jazz', '爵士'),
        ('classical', '古典'),
        ('folk', '民谣'),
        ('country', '乡村'),
        ('blues', '蓝调'),
        ('hiphop', '嘻哈'),
        ('heavy_metal', '重金属'),
        ('electronic', '电子'),
    ]
    name = models.CharField(max_length=64)
    singer = models.CharField(max_length=64)
    url = models.CharField(max_length=256)
    lyric_url = models.CharField(max_length=256, blank=True, null=True)
    count = models.IntegerField(default=0)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='pop')
    pic_url = models.CharField(max_length=256, blank=True, null=True)
    publish_date = models.DateField(null=True, blank=True)


# 用户听过歌曲的次数记录
class UserSongCount(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    song_name = models.CharField(max_length=200)
    count = models.IntegerField(default=0)


# 用户听过不同种类的音乐的次数，用于相似度计算
class UserMusicCount(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE)
    pop_count = models.IntegerField(default=0)
    rock_count = models.IntegerField(default=0)
    jazz_count = models.IntegerField(default=0)
    classical_count = models.IntegerField(default=0)
    folk_count = models.IntegerField(default=0)
    country_count = models.IntegerField(default=0)
    blues_count = models.IntegerField(default=0)
    hiphop_count = models.IntegerField(default=0)
    heavy_metal_count = models.IntegerField(default=0)
    electronic_count = models.IntegerField(default=0)


class UserSimilarity(models.Model):
    user1 = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name='similarities_as_user1')
    user2 = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name='similarities_as_user2')
    similarity = models.FloatField()


class MusicSimilarity(models.Model):
    music = models.ForeignKey(Music, on_delete=models.CASCADE, related_name='music')
    similar_music = models.ForeignKey(Music, on_delete=models.CASCADE, related_name='similar_music')
    similarity = models.FloatField()
    rank = models.IntegerField()

class Comment(models.Model):
    user = models.ForeignKey(UserInfo, related_name='usercomments', on_delete=models.CASCADE)
    music = models.ForeignKey(Music, related_name='musiccomments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    like_count = models.IntegerField(default=0)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.created_at}'

    class Meta:
        ordering = ['-created_at']


class CommentLike(models.Model):
    user = models.ForeignKey(UserInfo, on_delete=models.CASCADE, related_name='liked_comments')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    is_liked = models.BooleanField(default=True)


@receiver(post_save, sender=UserInfo)
def create_user_music_count(sender, instance, created, **kwargs):
    if created:
        UserMusicCount.objects.create(user=instance)
