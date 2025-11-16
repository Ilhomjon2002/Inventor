from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserRole(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('WAREHOUSE_MANAGER', 'Ombor xo\'jayini'),
        ('SELLER', 'Sotuvchi'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    warehouse = models.ForeignKey('inventor.Warehouse', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    company_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    telegram = models.CharField(max_length=100, blank=True)
    is_vip = models.BooleanField(default=False)
    monthly_payment = models.DecimalField(max_digits=10, decimal_places=2, default=300000)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    is_blocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.company_name}"
    
    def is_payment_due(self):
        if not self.last_payment_date:
            return True
        return timezone.now() > self.last_payment_date + timedelta(days=31)
    
    def days_until_block(self):
        if not self.last_payment_date:
            return 0
        days_passed = (timezone.now() - self.last_payment_date).days
        return max(0, 33 - days_passed)
    
    def get_payment_status(self):
        if self.is_payment_due():
            return {
                'status': 'due',
                'message': f"To'lanmagan: -{self.monthly_payment:,} so'm",
                'amount_due': -self.monthly_payment
            }
        else:
            return {
                'status': 'paid',
                'message': f"To'langan: 0 so'm",
                'amount_due': 0
            }

class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=(
        ('PENDING', 'Kutilmoqda'),
        ('PAID', 'To\'langan'),
        ('FAILED', 'Xatolik'),
    ), default='PENDING')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.amount} - {self.status}"

class Debt(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='debts')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    debt_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=(
        ('PENDING', 'Qarzdor'),
        ('PARTIAL', 'Qisman to\'langan'),
        ('PAID', 'To\'langan'),
    ), default='PENDING')
    
    def remaining_debt(self):
        return self.total_amount - self.paid_amount
    
    def __str__(self):
        return f"{self.seller.username} - {self.product.name} - {self.remaining_debt()}"

class UserLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=500)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"