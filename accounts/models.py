from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class CustomUser(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_ANALYST = 'analyst'
    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Administrator'),
        (ROLE_ANALYST, 'Data Analyst'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_ANALYST)
    phone = models.CharField(max_length=30, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_admin_user(self):
        return self.role == self.ROLE_ADMIN or self.is_superuser

    @property
    def is_analyst_user(self):
        return self.role == self.ROLE_ANALYST or self.is_admin_user

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=120)
    target_model = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=100, blank=True)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.user} - {self.action}"


class SystemNotification(models.Model):
    LEVEL_CHOICES = [
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info')
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"
