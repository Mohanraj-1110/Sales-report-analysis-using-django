from django.db import models
from django.utils import timezone

class Customer(models.Model):
    SEGMENT_CHOICES = [
        ('Champions', 'Champions'),
        ('Loyal Customers', 'Loyal Customers'),
        ('Potential Loyalists', 'Potential Loyalists'),
        ('Recent Customers', 'Recent Customers'),
        ('At Risk', 'At Risk'),
        ('Lost', 'Lost'),
        ('New Customer', 'New Customer'),
    ]

    customer_id = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='IN', db_index=True)
    postal_code = models.CharField(max_length=50, blank=True)

    # RFM Analytics Fields
    recency_days = models.IntegerField(default=0, help_text="Days since last order")
    frequency_orders = models.IntegerField(default=0, help_text="Total lifetime orders")
    monetary_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.00, help_text="Total lifetime spend")
    average_order_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    rfm_score = models.CharField(max_length=10, blank=True)
    segment = models.CharField(max_length=50, choices=SEGMENT_CHOICES, default='New Customer', db_index=True)

    first_order_date = models.DateField(null=True, blank=True)
    last_order_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-monetary_total']
        indexes = [
            models.Index(fields=['customer_id']),
            models.Index(fields=['segment']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        return f"{self.customer_id} - {self.name or 'Customer'}"
