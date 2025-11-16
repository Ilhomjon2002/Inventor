from django.contrib import admin
from .models import UserRole, UserProfile, Payment, Debt, UserLog

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'warehouse', 'created_at']
    list_filter = ['role', 'created_at']

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company_name', 'phone', 'is_vip', 'monthly_payment', 'last_payment_date', 'is_blocked']
    list_filter = ['is_vip', 'is_blocked']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'payment_date', 'status']
    list_filter = ['status', 'payment_date']

@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ['seller', 'product', 'quantity', 'total_amount', 'paid_amount', 'debt_date', 'status']
    list_filter = ['status', 'debt_date']

@admin.register(UserLog)
class UserLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'timestamp', 'ip_address']
    list_filter = ['timestamp']