from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('user', 'Обычный пользователь'),
        ('admin', 'Администратор'),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=5, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return self.username

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.title