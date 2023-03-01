from django.db import models


class Profile(models.Model):
    full_name = models.CharField(max_length=128)
    bio = models.TextField(max_length=512)
    avatar = models.BinaryField()

#todo delete profile when user deletes

class User(models.Model):
    mail = models.CharField(max_length=64, unique=True, null=False)
    pass_hash = models.CharField(max_length=512)
    profile_id = models.OneToOneField(Profile, on_delete=models.CASCADE, null=True)


class Post(models.Model):
    # post_id = models.AutoField(primary_key=True)
    profile_id = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    tag = models.TextField(max_length=256)
    date = models.DateTimeField(auto_now_add=True)
    vote_id = models.ForeignKey('Vote', on_delete=models.CASCADE)


class Vote(models.Model):
    profile_id = models.OneToOneField(Profile, related_name='votes', on_delete=models.CASCADE)
    post_id = models.OneToOneField(Post, related_name='votes', on_delete=models.CASCADE)
    vote = models.BooleanField()

    class Meta:
        unique_together = ('profile_id', 'post_id')


class Images(models.Model):
    image = models.BinaryField()
    post_id = models.ForeignKey(Post, on_delete=models.CASCADE)
