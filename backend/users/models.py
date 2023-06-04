from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(max_length=254, unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    user = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE,
        related_name='follower'
    )
    following = models.ForeignKey(
        to=CustomUser,
        on_delete=models.CASCADE,
        related_name='following'
    )

    def __str__(self):
        return f'{self.user} | {self.following}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_subscribers'
            )
        ]
