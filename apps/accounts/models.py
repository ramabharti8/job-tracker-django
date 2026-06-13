from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Admin"

    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.USER)
    bio = models.TextField(blank=True)
    linkedin_url = models.URLField(blank=True)
    target_role = models.CharField(max_length=100, blank=True)
    target_salary = models.PositiveIntegerField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def display_name(self):
        return self.full_name or self.email.split("@")[0]

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
