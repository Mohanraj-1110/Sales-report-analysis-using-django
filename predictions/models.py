from django.db import models
from django.conf import settings
from customers.models import Customer

class MLModelRecord(models.Model):
    MODEL_TYPE_CHOICES = [
        ('repurchase_classifier', 'Customer Repurchase Classifier'),
        ('sales_forecaster', 'Sales Forecast Regressor'),
    ]

    name = models.CharField(max_length=150)
    model_type = models.CharField(max_length=50, choices=MODEL_TYPE_CHOICES)
    algorithm = models.CharField(max_length=100)
    version = models.CharField(max_length=50, default='1.0.0')
    file_path = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    metrics = models.JSONField(default=dict, blank=True)
    training_sample_count = models.IntegerField(default=0)
    feature_names = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    trained_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    trained_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-trained_at']

    def __str__(self):
        return f"{self.name} v{self.version} ({self.algorithm}) - {'Active' if self.is_active else 'Inactive'}"


class CustomerPrediction(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='predictions')
    model_record = models.ForeignKey(MLModelRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='customer_predictions')
    purchase_probability = models.FloatField(help_text="Probability of purchase between 0.0 and 1.0")
    is_likely_to_purchase = models.BooleanField(default=False)
    risk_segment = models.CharField(max_length=50, default='Moderate')
    feature_contributions = models.JSONField(default=dict, blank=True)
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-predicted_at']
        indexes = [
            models.Index(fields=['customer']),
            models.Index(fields=['is_likely_to_purchase']),
            models.Index(fields=['risk_segment']),
        ]

    def __str__(self):
        return f"{self.customer.customer_id} - {self.purchase_probability * 100:.1f}% ({'Likely' if self.is_likely_to_purchase else 'Less Likely'})"
