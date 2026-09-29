from django.db import models
from customers.models import Customer
from products.models import Product

class Order(models.Model):
    STATUS_CHOICES = [
        ('Delivered', 'Delivered'),
        ('Shipped', 'Shipped'),
        ('Pending', 'Pending'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    ]

    order_id = models.CharField(max_length=100, unique=True, db_index=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateField(db_index=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Shipped', db_index=True)
    fulfilment = models.CharField(max_length=50, blank=True)
    sales_channel = models.CharField(max_length=50, default='Online Retail')
    ship_service_level = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, default='INR')
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    total_quantity = models.IntegerField(default=0)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=50, blank=True)
    shipping_country = models.CharField(max_length=100, default='IN', db_index=True)
    is_b2b = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-order_date', '-id']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['order_date']),
            models.Index(fields=['status']),
            models.Index(fields=['shipping_country']),
        ]

    def __str__(self):
        return f"Order #{self.order_id} - {self.customer.customer_id} ({self.total_amount} {self.currency})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name='order_items')
    sku = models.CharField(max_length=100, blank=True)
    product_name = models.CharField(max_length=255, blank=True)
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.quantity}x {self.sku or self.product_name} in {self.order.order_id}"
