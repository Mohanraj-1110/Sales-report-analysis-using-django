from django.db import models
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    ]

    sku = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    style = models.CharField(max_length=100, blank=True)
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    asin = models.CharField(max_length=50, blank=True)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    stock_quantity = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"
