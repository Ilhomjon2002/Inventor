import os
from celery import Celery
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from users.models import UserProfile, UserRole
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory_system.settings')

app = Celery('inventory_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task
def check_payment_status():
    """Check payment status and block users if payment is overdue"""
    profiles = UserProfile.objects.filter(is_blocked=False)
    
    for profile in profiles:
        if profile.is_payment_due():
            days_until_block = profile.days_until_block()
            
            if days_until_block == 1:
                # Send warning notification
                send_payment_warning.delay(profile.user.id)
            elif days_until_block <= 0:
                # Block user and related sellers
                profile.is_blocked = True
                profile.save()
                
                # Block related sellers
                if hasattr(profile.user, 'userrole'):
                    warehouse = profile.user.userrole.warehouse
                    if warehouse:
                        seller_roles = UserRole.objects.filter(warehouse=warehouse, role='SELLER')
                        for role in seller_roles:
                            role.user.userprofile.is_blocked = True
                            role.user.userprofile.save()
                
                send_block_notification.delay(profile.user.id)

@app.task
def send_payment_warning(user_id):
    """Send payment warning notification"""
    # Implement notification logic (email, telegram, etc.)
    pass

@app.task
def send_block_notification(user_id):
    """Send block notification"""
    # Implement notification logic
    pass