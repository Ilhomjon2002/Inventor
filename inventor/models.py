from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from products.models import Product

class Warehouse(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_total_products(self):
        return Product.objects.filter(warehouse=self).count()
    
    def get_total_value(self):
        products = Product.objects.filter(warehouse=self)
        return sum(product.price * product.stock_quantity for product in products if product.price)

class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_info = models.TextField()
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('IN', 'Kirim'),
        ('OUT_SALE', 'Sotuv'),
        ('OUT_DAMAGED', 'Buzilgan'),
        ('OUT_EXPIRED', 'Yaroqsiz'),
    )
    
    PAYMENT_TYPES = (
        ('CASH', 'Naqd'),
        ('DEBT', 'Qarz'),
        ('CARD', 'Karta'),
    )
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    description = models.TextField(blank=True)
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPES, default='CASH')
    customer_name = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.product.name} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Update product stock based on transaction type
        if self.transaction_type == 'IN':
            self.product.stock_quantity += self.quantity
        else:
            self.product.stock_quantity -= self.quantity
        self.product.save()
        super().save(*args, **kwargs)

class Report(models.Model):
    REPORT_TYPES = (
        ('DAILY', 'Kunlik'),
        ('WEEKLY', 'Haftalik'),
        ('MONTHLY', 'Oylik'),
        ('YEARLY', 'Yillik'),
    )
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    generated_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    data = models.JSONField(default=dict)  # Store report data as JSON
    
    def __str__(self):
        return f"{self.report_type} Hisobot - {self.generated_at}"

class Settings(models.Model):
    currency = models.CharField(max_length=10, default='UZS')
    backup_file = models.CharField(max_length=255, blank=True, null=True)
    last_backup = models.DateTimeField(null=True, blank=True)
    monthly_payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=300000)
    
    def __str__(self):
        return f"Sozlamalar - Valyuta: {self.currency}"