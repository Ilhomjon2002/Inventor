from django.db import models
from django.contrib.auth.models import User

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    UNIT_CHOICES = (
        ('kg', 'kg'),
        ('box', 'Karopka'),
        ('l', 'Litr'),
        ('m', 'Metr'),
        ('ton', 'Tonna'),
        ('piece', 'Dona'),
        ('pack', 'Pochka'),
    )
    
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    barcode = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    min_stock = models.PositiveIntegerField(default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='piece')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    supplier = models.ForeignKey('inventor.Supplier', on_delete=models.SET_NULL, null=True, blank=True)
    warehouse = models.ForeignKey('inventor.Warehouse', on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock
    
    class Meta:
        ordering = ['name']