from django.db import models
from django.conf import settings

class DatasetUpload(models.Model):
    STATUS_CHOICES = [
        ('Uploaded', 'Uploaded'),
        ('Validating', 'Validating'),
        ('Validated', 'Validated'),
        ('Processing', 'Processing'),
        ('Imported', 'Imported'),
        ('Failed', 'Failed'),
    ]

    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='datasets/raw/')
    file_type = models.CharField(max_length=20, default='CSV')
    file_size = models.BigIntegerField(default=0)
    total_rows = models.IntegerField(default=0)
    valid_rows = models.IntegerField(default=0)
    invalid_rows = models.IntegerField(default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Uploaded')
    
    detected_columns = models.JSONField(default=list, blank=True)
    column_mapping = models.JSONField(default=dict, blank=True)
    validation_summary = models.JSONField(default=dict, blank=True)
    cleaning_summary = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='datasets')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.name} ({self.status}) - {self.total_rows} rows"
