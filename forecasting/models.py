from django.db import models
from predictions.models import MLModelRecord

class SalesForecastRecord(models.Model):
    model_record = models.ForeignKey(MLModelRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name='forecasts')
    forecast_date = models.DateField(db_index=True)
    horizon_days = models.IntegerField(default=30)
    predicted_revenue = models.DecimalField(max_digits=14, decimal_places=2)
    predicted_orders = models.IntegerField(default=0)
    lower_bound = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    upper_bound = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['forecast_date']
        indexes = [
            models.Index(fields=['forecast_date']),
            models.Index(fields=['horizon_days']),
        ]

    def __str__(self):
        return f"{self.forecast_date} -> {self.predicted_revenue} (Horizon {self.horizon_days}d)"
