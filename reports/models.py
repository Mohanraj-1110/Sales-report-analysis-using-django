from django.db import models
from django.conf import settings

class GeneratedReport(models.Model):
    REPORT_TYPES = [
        ('sales', 'Sales Summary Report'),
        ('customer', 'Customer RFM Analysis Report'),
        ('product', 'Product Performance Report'),
        ('prediction', 'Repurchase Prediction Report'),
        ('forecast', 'Sales Forecast Report'),
    ]

    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel (XLSX)'),
        ('html', 'Interactive HTML'),
    ]

    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='csv')
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    filters_applied = models.JSONField(default=dict, blank=True)
    row_count = models.IntegerField(default=0)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reports')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_report_type_display()} - {self.format.upper()})"
