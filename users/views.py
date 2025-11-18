from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from .models import UserRole, UserProfile, Payment, Debt, UserLog
from inventor.models import *
from products.models import *
from django.http import HttpResponse, JsonResponse
import pandas as pd
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q
import json



def handler404(request, exception):
    return render(request, 'users/404.html', status=404)

def handler500(request):
    return render(request, 'users/500.html', status=500)


# Dekoratorlar
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            if request.user.userrole.role == 'ADMIN':
                return view_func(request, *args, **kwargs)
        except UserRole.DoesNotExist:
            pass
        messages.error(request, "Sizga bu sahifaga kirish uchun ruxsat yo'q!")
        return redirect('dashboard')
    return wrapper

def warehouse_manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            if request.user.userrole.role in ['ADMIN', 'WAREHOUSE_MANAGER']:
                return view_func(request, *args, **kwargs)
        except UserRole.DoesNotExist:
            pass
        messages.error(request, "Sizga bu sahifaga kirish uchun ruxsat yo'q!")
        return redirect('dashboard')
    return wrapper

def seller_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            if request.user.userrole.role in ['ADMIN', 'SELLER']:
                return view_func(request, *args, **kwargs)
        except UserRole.DoesNotExist:
            pass
        messages.error(request, "Sizga bu sahifaga kirish uchun ruxsat yo'q!")
        return redirect('dashboard')
    return wrapper

# Auth views
@login_required
def profile_view(request):
    """
    Foydalanuvchi profilini ko'rsatish funksiyasi.
    UserProfile, UserRole va Qarzdorlik (Debt) ma'lumotlarini templatega uzatadi.
    """
    try:
        # Get the related profile and role objects
        profile = UserProfile.objects.get(user=request.user)
        role = UserRole.objects.get(user=request.user)
        
        # Calculate payment status (using the method defined in your UserProfile model)
        payment_status = profile.get_payment_status()
        
        # Fetch user's debts (if they are a seller)
        debts = []
        if role.role == 'SELLER':
            # We fetch all pending/partial debts for the seller
            debts = Debt.objects.filter(
                seller=request.user, 
                status__in=['PENDING', 'PARTIAL']
            ).select_related('product') # Optimizing query to get product name
            
    except UserProfile.DoesNotExist:
        profile = None
        payment_status = {'status': 'error', 'message': "Profil topilmadi."}
        debts = []
    except UserRole.DoesNotExist:
        role = None
    
    context = {
        'user': request.user,
        'profile': profile,
        'role': role,
        'payment_status': payment_status,
        'debts': debts,
    }
    
    return render(request, 'users/profile.html', context)

def logout_view(request):
    """
    Foydalanuvchini tizimdan chiqarish va asosiy sahifaga yo'naltirish funksiyasi.
    """
    # Use Django's built-in logout function
    logout(request)
    # Redirect to the home page or login page after logout
    return redirect('users:login') # Assumes you have a URL named 'login'

# Admin views
@login_required
@admin_required
def admin_dashboard(request):
    warehouse_managers = UserRole.objects.filter(role='WAREHOUSE_MANAGER')
    total_warehouses = Warehouse.objects.count()
    total_sellers = UserRole.objects.filter(role='SELLER').count()
    
    # To'lov statistikasi
    pending_payments = Payment.objects.filter(status='PENDING')
    total_revenue = Payment.objects.filter(status='PAID').aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Block qilingan foydalanuvchilar
    blocked_users = UserProfile.objects.filter(is_blocked=True)
    
    context = {
        'warehouse_managers': warehouse_managers,
        'total_warehouses': total_warehouses,
        'total_sellers': total_sellers,
        'pending_payments': pending_payments,
        'total_revenue': total_revenue,
        'blocked_users': blocked_users,
    }
    return render(request, 'users/admin_dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user is blocked
            try:
                profile = user.userprofile
                if profile.is_blocked:
                    messages.error(request, "Hisobingiz bloklangan! Iltimos, admin bilan bog'laning.")
                    return redirect('login')
            except UserProfile.DoesNotExist:
                pass
            
            login(request, user)
            UserLog.objects.create(user=user, action="Tizimga kirdi")
            
            # Redirect based on role
            try:
                role = user.userrole.role
                if role == 'ADMIN':
                    return redirect('users:admin_dashboard')
                elif role == 'WAREHOUSE_MANAGER':
                    return redirect('users:warehouse_manager_dashboard')
                elif role == 'SELLER':
                    return redirect('users:seller_dashboard')
            except UserRole.DoesNotExist:
                pass
            
            return redirect('dashboard')
        else:
            messages.error(request, "Login yoki parol noto'g'ri!")
    
    return render(request, 'users/login.html')


@login_required
@admin_required
def create_warehouse_manager(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        company_name = request.POST.get('company_name')
        phone = request.POST.get('phone')
        location = request.POST.get('location')
        monthly_payment = request.POST.get('monthly_payment', 300000)
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ushbu login band!")
            return redirect('create_warehouse_manager')
        
        # Yangi foydalanuvchi yaratish
        user = User.objects.create_user(
            username=username, 
            password=password,
            first_name=company_name
        )
        
        # Profil yaratish
        profile = UserProfile.objects.create(
            user=user,
            company_name=company_name,
            phone=phone,
            monthly_payment=monthly_payment
        )
        
        # Warehouse yaratish
        warehouse = Warehouse.objects.create(
            name=company_name,
            location=location
        )
        
        # Rol berish
        UserRole.objects.create(
            user=user, 
            role='WAREHOUSE_MANAGER',
            warehouse=warehouse
        )
        
        UserLog.objects.create(
            user=request.user, 
            action=f"Yangi ombor xo'jayini yaratdi: {company_name}"
        )
        messages.success(request, "Ombor xo'jayini muvaffaqiyatli yaratildi!")
        return redirect('users:admin_dashboard')
    
    return render(request, 'users/create_warehouse_manager.html')

@login_required
@admin_required
def payment_management(request):
    payments = Payment.objects.all().order_by('-payment_date')
    
    if request.method == 'POST':
        payment_id = request.POST.get('payment_id')
        action = request.POST.get('action')
        payment = get_object_or_404(Payment, id=payment_id)
        
        if action == 'confirm':
            payment.status = 'PAID'
            payment.user.userprofile.last_payment_date = timezone.now()
            payment.user.userprofile.is_blocked = False
            payment.user.userprofile.save()
            payment.save()
            
            # Blokdan chiqarish
            seller_roles = UserRole.objects.filter(warehouse=payment.user.userrole.warehouse)
            for role in seller_roles:
                role.user.userprofile.is_blocked = False
                role.user.userprofile.save()
            
            messages.success(request, "To'lov tasdiqlandi va blok olib tashlandi!")
        elif action == 'block':
            payment.user.userprofile.is_blocked = True
            payment.user.userprofile.save()
            
            # Sotuvchilarni ham bloklash
            seller_roles = UserRole.objects.filter(warehouse=payment.user.userrole.warehouse)
            for role in seller_roles:
                role.user.userprofile.is_blocked = True
                role.user.userprofile.save()
            
            messages.warning(request, "Foydalanuvchi va uning sotuvchilari bloklandi!")
    
    return render(request, 'admin/payment_management.html', {'payments': payments})

# Ombor xo'jayini views
from django.db import IntegrityError, transaction
@login_required
@warehouse_manager_required
def warehouse_manager_dashboard(request):
    user_profile = request.user.userprofile
    warehouse = request.user.userrole.warehouse
    
    payment_status = user_profile.get_payment_status()
    days_until_block = user_profile.days_until_block()
    
    # Statistikalar
    sellers = UserRole.objects.filter(warehouse=warehouse, role='SELLER')
    total_products = Product.objects.filter(warehouse=warehouse).count()
    recent_transactions = Transaction.objects.filter(warehouse=warehouse).order_by('-date')[:10]
    
    # Low stock products
    low_stock_products = Product.objects.filter(
        warehouse=warehouse,
        stock_quantity__lte=models.F('min_stock')
    )
    
    context = {
        'user_profile': user_profile,
        'warehouse': warehouse,
        'payment_status': payment_status,
        'days_until_block': days_until_block,
        'sellers': sellers,
        'total_products': total_products,
        'recent_transactions': recent_transactions,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'users/warehouse_manager_dashboard.html', context)




from django.contrib.auth import get_user_model
from django.db import transaction # <<-- YANGI IMPORT

# Modellar importi (Sizning loyihangizga qarab nomlar boshqacha bo'lishi mumkin)
# from .models import UserProfile, UserRole, UserLog 
# from inventor.decorators import warehouse_manager_required 

User = get_user_model()

# Funksiyani atomik tranzaksiya bilan o'rash
@transaction.atomic
@login_required
@warehouse_manager_required
def create_seller(request):
    # Foydalanuvchi role orqali ombor ma'lumotlarini olish
    # UserRole.warehouse maydoni None bo'lmasligi kerak deb faraz qilinadi
    warehouse = request.user.userrole.warehouse
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        # phone = request.POST.get('phone')
        
        # 1. Login bandligini tekshirish (bu tranzaksiyadan tashqarida ham xavfsiz)
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ushbu login band!")
            # Tranzaksiya ichida bo'lgani uchun, agar bu yerda redirect qilsa, 
            # bazaga hech narsa yozilmagan bo'ladi.
            return redirect('users:create_seller')
        
        # 2. User yaratish
        # Agar bu qatordan keyingi har qanday qator xato bersa, yaratilgan user o'chiriladi.
        user = User.objects.create_user(
            username=username, 
            password=password,
            first_name=first_name
        )
        
        # 3. Profil yaratish
        # UserProfile.objects.create(user=user)
        
        # 4. Rol berish
        UserRole.objects.create(
            user=user, 
            role='SELLER',
            warehouse=warehouse
        )
        
        # 5. Log yozish
        UserLog.objects.create(
            user=request.user, 
            action=f"Yangi sotuvchi yaratdi: {first_name} ({username})"
        )
        
        messages.success(request, "Sotuvchi muvaffaqiyatli yaratildi!")
        return redirect('users:warehouse_manager_dashboard')
    
    return render(request, 'users/create_seller.html')

@login_required
@warehouse_manager_required
def seller_statistics(request, seller_id):
    seller = get_object_or_404(User, id=seller_id)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filtrlash
    transactions = Transaction.objects.filter(user=seller)
    
    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        transactions = transactions.filter(
            date__gte=start_date,
            date__lte=end_date
        )
    
    # Statistikalar
    total_sales = transactions.filter(transaction_type='OUT_SALE').count()
    total_quantity = transactions.filter(transaction_type='OUT_SALE').aggregate(Sum('quantity'))['quantity__sum'] or 0
    total_revenue = sum(t.quantity * t.product.price for t in transactions.filter(transaction_type='OUT_SALE') if t.product.price)
    
    # Qarzdorlik ma'lumotlari
    debts = Debt.objects.filter(seller=seller)
    total_debt = sum(debt.remaining_debt() for debt in debts)
    
    context = {
        'seller': seller,
        'transactions': transactions,
        'total_sales': total_sales,
        'total_quantity': total_quantity,
        'total_revenue': total_revenue,
        'debts': debts,
        'total_debt': total_debt,
        'start_date': start_date.strftime('%Y-%m-%d') if start_date else '',
        'end_date': end_date.strftime('%Y-%m-%d') if end_date else '',
    }
    return render(request, 'users/seller_statistics.html', context)

# Sotuvchi views
@login_required
@seller_required
def seller_dashboard(request):
    warehouse = request.user.userrole.warehouse
    products = Product.objects.filter(warehouse=warehouse)
    
    # Sotuvchi tarixi
    my_transactions = Transaction.objects.filter(user=request.user).order_by('-date')[:10]
    
    # Qarzdorlik ma'lumotlari
    my_debts = Debt.objects.filter(seller=request.user)
    
    context = {
        'products': products,
        'my_transactions': my_transactions,
        'my_debts': my_debts,
        'warehouse': warehouse,
    }
    return render(request, 'users/seller_dashboard.html', context)

@login_required
@seller_required
def take_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    warehouse = request.user.userrole.warehouse
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        payment_type = request.POST.get('payment_type')
        customer_name = request.POST.get('customer_name', '')
        
        if product.stock_quantity < quantity:
            messages.error(request, "Omborda yetarli mahsulot yo'q!")
            return redirect('users:seller_dashboard')
        
        # Mahsulotni chiqim qilish
        product.stock_quantity -= quantity
        product.save()
        
        # Tranzaksiya yaratish
        transaction = Transaction.objects.create(
            product=product,
            warehouse=warehouse,
            transaction_type='OUT_SALE',
            quantity=quantity,
            user=request.user,
            description=f"Xaridor: {customer_name}" if customer_name else ""
        )
        
        # Agar qarz bo'lsa, qarzdorlik yozuvi yaratish
        if payment_type == 'DEBT':
            total_amount = quantity * product.price
            Debt.objects.create(
                seller=request.user,
                product=product,
                quantity=quantity,
                total_amount=total_amount,
                paid_amount=0,
                description=f"Xaridor: {customer_name}" if customer_name else ""
            )
        
        UserLog.objects.create(
            user=request.user, 
            action=f"Mahsulot oldi: {product.name} - {quantity} dona"
        )
        messages.success(request, "Mahsulot muvaffaqiyatli olingan!")
        return redirect('users:seller_dashboard')
    
    return render(request, 'products/take_product.html', {'product': product})


# Umumiy dashboard
@login_required
def dashboard(request):
    try:
        role = request.user.userrole.role
        if role == 'ADMIN':
            return redirect('users:admin_dashboard')
        elif role == 'WAREHOUSE_MANAGER':
            return redirect('users:warehouse_manager_dashboard')
        elif role == 'SELLER':
            return redirect('users:seller_dashboard')
    except UserRole.DoesNotExist:
        pass
    
    return render(request, 'products/dashboard.html')