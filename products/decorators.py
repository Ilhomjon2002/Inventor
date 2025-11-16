# users/decorators.py
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Iltimos, avval tizimga kiring!")
            return redirect('users:login')
        
        # Check if user has admin role
        if hasattr(request.user, 'userrole') and request.user.userrole.role == 'ADMIN':
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Sizga bu sahifaga kirish uchun ruxsat yo'q!")
        return redirect('users:dashboard')
    return wrapper

def warehouse_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Iltimos, avval tizimga kiring!")
            return redirect('users:login')
        
        # Check if user has warehouse manager or admin role
        if hasattr(request.user, 'userrole') and request.user.userrole.role in ['ADMIN', 'WAREHOUSE_MANAGER']:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Sizga bu sahifaga kirish uchun ruxsat yo'q!")
        return redirect('users:dashboard')
    return wrapper

def seller_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Iltimos, avval tizimga kiring!")
            return redirect('users:login')
        
        # Check if user has seller, warehouse manager or admin role
        if hasattr(request.user, 'userrole') and request.user.userrole.role in ['ADMIN', 'WAREHOUSE_MANAGER', 'SELLER']:
            return view_func(request, *args, **kwargs)
        
        messages.error(request, "Sizga bu sahifaga kirish uchun ruxsat yo'q!")
        return redirect('users:dashboard')
    return wrapper

def payment_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        
        # Check if user has paid
        if hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            if profile.is_blocked:
                messages.error(request, "Sizning hisobingiz bloklangan! Iltimos, to'lov qiling.")
                return redirect('users:make_payment')
            if profile.is_payment_due():
                messages.warning(request, "To'lov muddati yaqinlashmoqda! Iltimos, to'lov qiling.")
        
        return view_func(request, *args, **kwargs)
    return wrapper