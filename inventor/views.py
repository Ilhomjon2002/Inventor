from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from users.decorators import admin_required, warehouse_manager_required, seller_required
from django.contrib import messages
from .models import Warehouse, Supplier, Transaction, Report, Settings
from products.models import Product
from users.models import UserLog, UserRole
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
import pandas as pd
from django.http import HttpResponse
import os
from django.conf import settings as django_settings
from decimal import Decimal, InvalidOperation
import json
from django.core.paginator import Paginator
from django.db.models import Q
# from datetime import datetame

@login_required
def warehouse_list(request):
    warehouses = Warehouse.objects.all()
    UserLog.objects.create(user=request.user, action="Omborlar ro'yxatini ko'rdi")
    return render(request, 'inventor/warehouse_list.html', {'warehouses': warehouses})

@login_required
def warehouse_stock(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    products = Product.objects.filter(warehouse=warehouse)
    
    UserLog.objects.create(user=request.user, action=f"Ombor zaxirasini ko'rdi: {warehouse.name}")
    return render(request, 'inventor/warehouse_stock.html', {
        'warehouse': warehouse,
        'products': products
    })

@login_required
@admin_required
def warehouse_edit(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    
    if request.method == 'POST':
        warehouse.name = request.POST.get('name')
        warehouse.location = request.POST.get('location')
        warehouse.save()
        
        UserLog.objects.create(user=request.user, action=f"Omborni tahrirladi: {warehouse.name}")
        messages.success(request, "Ombor muvaffaqiyatli tahrirlandi!")
        return redirect('inventor:warehouse_list')
    
    return render(request, 'inventor/warehouse_form.html', {'warehouse': warehouse})


@login_required
@admin_required
def warehouse_delete(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    warehouse_name = warehouse.name
    warehouse.delete()
    
    UserLog.objects.create(user=request.user, action=f"Omborni o'chirdi: {warehouse_name}")
    messages.success(request, "Ombor muvaffaqiyatli o'chirildi!")
    return redirect('inventor:warehouse_list')

@login_required
def transaction_create(request):
    if request.method == 'POST':
        product_id = request.POST.get('product')
        warehouse_id = request.POST.get('warehouse')
        transaction_type = request.POST.get('transaction_type')
        quantity = int(request.POST.get('quantity'))
        description = request.POST.get('description', '')
        
        product = get_object_or_404(Product, id=product_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id)
        
        # Create transaction
        transaction = Transaction.objects.create(
            product=product,
            warehouse=warehouse,
            transaction_type=transaction_type,
            quantity=quantity,
            user=request.user,
            description=description
        )
        
        UserLog.objects.create(user=request.user, action=f"Tranzaksiya amalga oshirdi: {transaction}")
        messages.success(request, "Tranzaksiya muvaffaqiyatli amalga oshirildi!")
        return redirect('inventor:transaction_history')
    
    products = Product.objects.all()
    warehouses = request.user.userrole.warehouse
    return render(request, 'inventor/transaction_create.html', {
        'products': products,
        'warehouses': warehouses
    })
import datetime
@login_required
def transaction_history(request):
    # Boshlang'ich so'rov
    transactions = Transaction.objects.all().order_by('-date')
    
    # Filter parametrlarini olish
    transaction_type = request.GET.get('type')
    # warehouse_id = request.GET.get('warehouse')
    warehouse_id = request.user.userrole.warehouse.id
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filterlarni qo'llash
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if warehouse_id:
        transactions = transactions.filter(warehouse_id=warehouse_id)
    
    if start_date:
        transactions = transactions.filter(date__gte=start_date)
    
    if end_date:
        # Kun oxirigacha filtrlash
        end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        end_date_obj = end_date_obj + datetime.timedelta(days=1)
        transactions = transactions.filter(date__lt=end_date_obj)
    
    # Statistikani hisoblash (pagination dan oldin)
    total_count = transactions.count()
    # in_count = transactions.filter(transaction_type='IN').count()
    # out_sale_count = transactions.filter(transaction_type='OUT_SALE').count()
    
    # Jami kirimni hisoblash
    out_sale_count = 0
    sale_transactions = transactions.filter(transaction_type='OUT_SALE')
    for transaction in sale_transactions:
        if transaction.product and transaction.product.price:
            out_sale_count += transaction.quantity * transaction.product.price

    # Jami chiqimni hisoblash
    in_count = 0
    sale_transactions = transactions.filter(transaction_type='IN')
    for transaction in sale_transactions:
        if transaction.product and transaction.product.price:
            in_count += transaction.quantity * transaction.product.price
    
    # Daromadni hisoblash
    total_revenue = out_sale_count-in_count
    
    # Pagination
    paginator = Paginator(transactions, 50)  # 50 ta element har bir sahifada
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    warehouses = request.user.userrole.warehouse
    
    UserLog.objects.create(user=request.user, action="Tranzaksiya tarixini ko'rdi")
    
    context = {
        'transactions': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'warehouse': warehouses,
        'stats': {
            'total_count': total_count,
            'in_count': in_count,
            'out_sale_count': out_sale_count,
            'total_revenue': total_revenue,
        }
    }
    
    return render(request, 'inventor/transaction_history.html', context)

@login_required
@warehouse_manager_required
def export_transactions(request):
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    transactions = Transaction.objects.all()
    
    if start_date and end_date:
        start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        transactions = transactions.filter(
            date__gte=start_date,
            date__lte=end_date
        )
    
    data = {
        'Sana': [t.date.strftime('%Y-%m-%d %H:%M') for t in transactions],
        'Mahsulot': [t.product.name for t in transactions],
        'Turi': [t.get_transaction_type_display() for t in transactions],
        'Miqdor': [t.quantity for t in transactions],
        'Narx': [float(t.product.price) if t.product.price else 0 for t in transactions],
        'Umumiy Summa': [float(t.quantity * (t.product.price if t.product.price else 0)) for t in transactions],
        'Foydalanuvchi': [t.user.username for t in transactions],
        'Toʻlov turi': [t.get_payment_type_display() for t in transactions],
        'Izoh': [t.description for t in transactions],
    }
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    filename = f"tranzaksiyalar_{timezone.now().strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    df.to_excel(response, index=False)
    
    UserLog.objects.create(user=request.user, action="Tranzaksiyalarni eksport qildi")
    return response


# Yetkazib beruvchilar view-lari
@login_required
@admin_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    UserLog.objects.create(user=request.user, action="Yetkazib beruvchilar ro'yxatini ko'rdi")
    return render(request, 'inventor/supplier_list.html', {'suppliers': suppliers})

@login_required
@admin_required
def supplier_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        contact_info = request.POST.get('contact_info')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')
        
        supplier = Supplier.objects.create(
            name=name,
            contact_info=contact_info,
            address=address,
            phone=phone
        )
        
        UserLog.objects.create(user=request.user, action=f"Yangi yetkazib beruvchi yaratdi: {name}")
        messages.success(request, "Yetkazib beruvchi muvaffaqiyatli yaratildi!")
        return redirect('inventor:supplier_list')
    
    return render(request, 'inventor/supplier_form.html')

@login_required
@admin_required
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    products = Product.objects.filter(supplier=supplier)
    
    context = {
        'supplier': supplier,
        'products': products,
    }
    return render(request, 'inventor/supplier_detail.html', context)

@login_required
@admin_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.contact_info = request.POST.get('contact_info')
        supplier.address = request.POST.get('address', '')
        supplier.phone = request.POST.get('phone', '')
        supplier.save()
        
        UserLog.objects.create(user=request.user, action=f"Yetkazib beruvchini tahrirladi: {supplier.name}")
        messages.success(request, "Yetkazib beruvchi muvaffaqiyatli tahrirlandi!")
        return redirect('inventor:supplier_list')
    
    return render(request, 'inventor/supplier_form.html', {'supplier': supplier})

@login_required
@admin_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    supplier_name = supplier.name
    supplier.delete()
    
    UserLog.objects.create(user=request.user, action=f"Yetkazib beruvchini o'chirdi: {supplier_name}")
    messages.success(request, "Yetkazib beruvchi muvaffaqiyatli o'chirildi!")
    return redirect('inventor:supplier_list')

@login_required
@admin_required
def supplier_products(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    products = Product.objects.filter(supplier=supplier)
    UserLog.objects.create(user=request.user, action=f"Yetkazib beruvchi mahsulotlarini ko'rdi: {supplier.name}")
    return render(request, 'inventor/supplier_products.html', {'supplier': supplier, 'products': products})

@login_required
@admin_required
def supplier_stats(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    transactions = Transaction.objects.filter(product__supplier=supplier, transaction_type='IN')
    total_delivered = sum(t.quantity for t in transactions)
    UserLog.objects.create(user=request.user, action=f"Yetkazib beruvchi statistikasini ko'rdi: {supplier.name}")
    return render(request, 'inventor/supplier_stats.html', {'supplier': supplier, 'total_delivered': total_delivered})


# Hisobotlar
@login_required
def report_generate(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        custom_start = request.POST.get('start_date')
        custom_end = request.POST.get('end_date')
        
        today = timezone.now()
        
        if report_type == 'DAILY':
            start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        elif report_type == 'WEEKLY':
            start_date = today - timedelta(days=today.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        elif report_type == 'MONTHLY':
            start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        elif report_type == 'YEARLY':
            start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = today
        else:  # CUSTOM
            start_date = timezone.make_aware(timezone.datetime.strptime(custom_start, '%Y-%m-%d'))
            end_date = timezone.make_aware(timezone.datetime.strptime(custom_end, '%Y-%m-%d'))
            end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            report_type = 'CUSTOM'
        
        # Collect report data
        transactions = Transaction.objects.filter(date__range=[start_date, end_date])
        
        # Total income ni hisoblash (Decimal ni float ga o'tkazish)
        total_income = 0
        sale_transactions = transactions.filter(transaction_type='OUT_SALE')
        for transaction in sale_transactions:
            if transaction.product and transaction.product.price:
                total_income += float(transaction.quantity) * float(transaction.product.price)
        
        # Top products (Decimal ni float ga o'tkazish)
        top_products_data = []
        top_products = transactions.filter(transaction_type='OUT_SALE')\
            .values('product__name')\
            .annotate(total_sold=Sum('quantity'))\
            .order_by('-total_sold')[:10]
        
        for product in top_products:
            top_products_data.append({
                'product_name': product['product__name'],
                'total_sold': float(product['total_sold']) if product['total_sold'] else 0.0
            })
        
        # Transaction by type
        transaction_by_type_data = []
        transaction_types = transactions.values('transaction_type')\
            .annotate(count=Count('id'))
        
        for trans_type in transaction_types:
            transaction_by_type_data.append({
                'transaction_type': trans_type['transaction_type'],
                'count': trans_type['count']
            })
        
        report_data = {
            'total_transactions': transactions.count(),
            'total_income': total_income,  # Endi bu float
            'top_products': top_products_data,
            'transaction_by_type': transaction_by_type_data,
        }
        
        report = Report.objects.create(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            user=request.user,
            data=report_data
        )
        
        UserLog.objects.create(user=request.user, action=f"Hisobot yaratdi: {report}")
        messages.success(request, "Hisobot muvaffaqiyatli yaratildi!")
        return redirect('inventor:report_detail', pk=report.pk)
    
    return render(request, 'inventor/report_generate.html')


@login_required
def report_list(request):
    reports = Report.objects.all().order_by('-generated_at')
    UserLog.objects.create(user=request.user, action="Hisobotlar ro'yxatini ko'rdi")
    return render(request, 'inventor/report_list.html', {'reports': reports})

@login_required
def report_detail(request, pk):
    report = get_object_or_404(Report, pk=pk)
    transactions = Transaction.objects.filter(
        date__gte=report.start_date, 
        date__lte=report.end_date
    )
    
    # Kunlar sonini hisoblash
    time_difference = report.end_date - report.start_date
    days_count = time_difference.days + 1
    
    # Faol foydalanuvchilar soni
    active_users_count = transactions.values('user').distinct().count()
    
    # O'rtacha chek va kunlik o'rtacha sotuvni hisoblash
    total_income = report.data.get('total_income', 0)
    total_transactions = report.data.get('total_transactions', 0)
    
    daily_avg = total_income / days_count if days_count > 0 and total_income else 0
    avg_check = total_income / total_transactions if total_transactions > 0 and total_income else 0
    
    context = {
        'report': report,
        'transactions': transactions,
        'report_data': report.data,
        'days_count': days_count,
        'active_users_count': active_users_count,
        'daily_avg': daily_avg,
        'avg_check': avg_check,
    }
    
    UserLog.objects.create(user=request.user, action=f"Hisobot tafsilotlarini ko'rdi: {report}")
    return render(request, 'inventor/report_detail.html', context)


@login_required
@admin_required
def settings_update(request):
    settings_obj, _ = Settings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        settings_obj.currency = request.POST.get('currency')
        settings_obj.monthly_payment_amount = request.POST.get('monthly_payment_amount', 300000)
        settings_obj.save()
        
        UserLog.objects.create(user=request.user, action=f"Sozlamalarni yangiladi: Valyuta - {settings_obj.currency}")
        messages.success(request, "Sozlamalar muvaffaqiyatli yangilandi!")
        return redirect('inventor:settings_update')
    
    return render(request, 'inventor/settings.html', {'settings': settings_obj})

@login_required
@admin_required
def bulk_price_update(request):
    if request.method == 'POST':
        try:
            percentage = Decimal(request.POST.get('percentage'))
        except (InvalidOperation, TypeError):
            messages.error(request, "Noto'g'ri foiz qiymati.")
            return redirect('inventor:bulk_price_update')

        products = Product.objects.all()
        updated_count = 0
        
        for product in products:
            if product.price:
                product.price *= (Decimal('1') + (percentage / Decimal('100')))
                product.save()
                updated_count += 1

        UserLog.objects.create(user=request.user, action=f"Narxlarni ommaviy tahrirladi: {percentage}%")
        messages.success(request, f"{updated_count} ta mahsulot narxi {percentage}% ga muvaffaqiyatli yangilandi!")
        return redirect('products:product_list')

    return render(request, 'inventor/bulk_price_update.html')

@login_required
@admin_required
def backup_database(request):
    settings_obj, _ = Settings.objects.get_or_create(id=1)
    db_path = os.path.join(django_settings.BASE_DIR, 'db.sqlite3')
    
    # Create backups directory if not exists
    backups_dir = os.path.join(django_settings.BASE_DIR, 'backups')
    os.makedirs(backups_dir, exist_ok=True)
    
    backup_path = os.path.join(backups_dir, f"backup_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sqlite3")

    try:
        with open(db_path, 'rb') as db_file, open(backup_path, 'wb') as backup_file:
            backup_file.write(db_file.read())

        settings_obj.backup_file = backup_path
        settings_obj.last_backup = timezone.now()
        settings_obj.save()

        UserLog.objects.create(user=request.user, action="Ma'lumotlar bazasi zaxira nusxasini yaratdi")
        messages.success(request, "Zaxira nusxa muvaffaqiyatli yaratildi!")
    except Exception as e:
        messages.error(request, f"Zaxira nusxa yaratishda xato: {str(e)}")
    
    return redirect('inventor:settings_update')

@login_required
@admin_required
def restore_database(request):
    settings_obj = get_object_or_404(Settings, id=1)
    
    if request.method == 'POST' and settings_obj.backup_file:
        db_path = os.path.join(django_settings.BASE_DIR, 'db.sqlite3')
        backup_file_path = settings_obj.backup_file
        
        try:
            if not os.path.exists(backup_file_path):
                messages.error(request, "Zaxira fayli topilmadi!")
                return redirect('inventor:settings_update')
            
            with open(backup_file_path, 'rb') as backup_file, open(db_path, 'wb') as db_file:
                db_file.write(backup_file.read())
            
            UserLog.objects.create(user=request.user, action="Ma'lumotlar bazasini tikladi")
            messages.success(request, "Ma'lumotlar bazasi muvaffaqiyatli tiklandi!")
            return redirect('inventor:settings_update')
        except Exception as e:
            messages.error(request, f"Tiklashda xato yuz berdi: {str(e)}")
            return redirect('inventor:settings_update')
    
    return render(request, 'inventor/restore_database.html', {'settings': settings_obj})


@login_required
@admin_required
def export_products(request):
    products = Product.objects.all()
    data = {
        'Nomi': [p.name for p in products],
        'Kategoriya': [p.category.name for p in products],
        'Shtrix-kod': [p.barcode for p in products],
        'Tavsif': [p.description for p in products],
        'Narxi': [p.price for p in products],
        'Minimal zaxira': [p.min_stock for p in products],
        'Zaxiradagi miqdor': [p.stock_quantity for p in products],
        'Yetkazib beruvchi': [p.supplier.name if p.supplier else '' for p in products],
    }
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="products.xlsx"'
    df.to_excel(response, index=False)
    UserLog.objects.create(user=request.user, action="Mahsulotlarni Excelga eksport qildi")
    return response

@login_required
@admin_required
def import_products(request):
    if request.method == 'POST':
        file = request.FILES['file']
        df = pd.read_excel(file)
        
        imported_count = 0
        updated_count = 0
        
        for _, row in df.iterrows():
            category_name = row.get('Kategoriya', '')
            if category_name:
                category, _ = Category.objects.get_or_create(name=category_name)
            else:
                category = None
            
            supplier_name = row.get('Yetkazib beruvchi', '')
            supplier = Supplier.objects.filter(name=supplier_name).first() if supplier_name else None
            
            barcode = row.get('Shtrix-kod', '')
            if barcode and Product.objects.filter(barcode=barcode).exists():
                # Update existing product
                product = Product.objects.get(barcode=barcode)
                product.name = row.get('Nomi', product.name)
                product.category = category
                product.description = row.get('Tavsif', product.description)
                product.price = row.get('Narxi', product.price)
                product.min_stock = row.get('Minimal zaxira', product.min_stock)
                product.stock_quantity = row.get('Zaxiradagi miqdor', product.stock_quantity)
                product.supplier = supplier
                product.save()
                updated_count += 1
            else:
                # Create new product
                Product.objects.create(
                    name=row.get('Nomi', ''),
                    category=category,
                    barcode=barcode,
                    description=row.get('Tavsif', ''),
                    price=row.get('Narxi', 0),
                    min_stock=row.get('Minimal zaxira', 0),
                    stock_quantity=row.get('Zaxiradagi miqdor', 0),
                    supplier=supplier
                )
                imported_count += 1
        
        UserLog.objects.create(user=request.user, action=f"Mahsulotlarni import qildi: {imported_count} yangi, {updated_count} yangilandi")
        messages.success(request, f"Mahsulotlar muvaffaqiyatli import qilindi! {imported_count} yangi, {updated_count} yangilandi")
        return redirect('products:product_list')
    
    return render(request, 'inventor/import_products.html')

# Qarzdorlik view-lari
@login_required
@warehouse_manager_required
def debt_list(request):
    debts = Debt.objects.all().order_by('-debt_date')
    return render(request, 'inventor/debt_list.html', {'debts': debts})

@login_required
@warehouse_manager_required
def debt_payment(request, pk):
    debt = get_object_or_404(Debt, pk=pk)
    
    if request.method == 'POST':
        payment_amount = Decimal(request.POST.get('payment_amount', 0))
        
        if payment_amount <= 0:
            messages.error(request, "Noto'g'ri to'lov miqdori!")
            return redirect('inventor:debt_list')
        
        debt.paid_amount += payment_amount
        
        if debt.paid_amount >= debt.total_amount:
            debt.status = 'PAID'
        elif debt.paid_amount > 0:
            debt.status = 'PARTIAL'
        
        debt.save()
        
        UserLog.objects.create(user=request.user, action=f"Qarz to'lovi: {debt.seller.username} - {payment_amount}")
        messages.success(request, f"{payment_amount} so'm muvaffaqiyatli to'landi!")
        return redirect('inventor:debt_list')
    
    return render(request, 'inventor/debt_payment.html', {'debt': debt})

@login_required
@warehouse_manager_required
def export_debts(request):
    debts = Debt.objects.all()
    
    data = {
        'Sotuvchi': [d.seller.username for d in debts],
        'Mahsulot': [d.product.name for d in debts],
        'Miqdor': [d.quantity for d in debts],
        'Umumiy summa': [float(d.total_amount) for d in debts],
        'Toʻlangan': [float(d.paid_amount) for d in debts],
        'Qolgan qarz': [float(d.remaining_debt()) for d in debts],
        'Holat': [d.get_status_display() for d in debts],
        'Sana': [d.debt_date.strftime('%Y-%m-%d') for d in debts],
    }
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="qarzdorlik.xlsx"'
    df.to_excel(response, index=False)
    
    UserLog.objects.create(user=request.user, action="Qarzdorlik ro'yxatini eksport qildi")
    return response

# Statistika view-lari
@login_required
def dashboard_statistics(request):
    total_warehouses = Warehouse.objects.count()
    total_products = Product.objects.count()
    total_transactions = Transaction.objects.count()
    
    total_revenue = Transaction.objects.filter(
        transaction_type='OUT_SALE'
    ).aggregate(
        total=Sum(F('quantity') * F('product__price'))
    )['total'] or 0
    
    low_stock_count = Product.objects.filter(stock_quantity__lte=F('min_stock')).count()
    
    context = {
        'total_warehouses': total_warehouses,
        'total_products': total_products,
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
        'low_stock_count': low_stock_count,
    }
    return render(request, 'inventor/dashboard_stats.html', context)

@login_required
def sales_statistics(request):
    # Sales statistics for the last 30 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    daily_sales = Transaction.objects.filter(
        transaction_type='OUT_SALE',
        date__range=[start_date, end_date]
    ).extra(
        {'date_only': "date(date)"}
    ).values('date_only').annotate(
        total_sales=Sum(F('quantity') * F('product__price')),
        total_quantity=Sum('quantity')
    ).order_by('date_only')
    
    context = {
        'daily_sales': list(daily_sales),
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'inventor/sales_statistics.html', context)

@login_required
def inventory_statistics(request):
    # Inventory statistics
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock_quantity__lte=F('min_stock'))
    out_of_stock_products = Product.objects.filter(stock_quantity=0)
    
    # Products by category
    products_by_category = Product.objects.values(
        'category__name'
    ).annotate(
        count=Count('id'),
        total_value=Sum(F('stock_quantity') * F('price'))
    ).order_by('-count')
    
    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'products_by_category': products_by_category,
    }
    return render(request, 'inventor/inventory_statistics.html', context)

# API view-lari
@login_required
def api_warehouse_stock(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    products = Product.objects.filter(warehouse=warehouse).values(
        'id', 'name', 'stock_quantity', 'min_stock', 'price'
    )
    
    data = {
        'warehouse': warehouse.name,
        'products': list(products)
    }
    
    return HttpResponse(json.dumps(data, default=str), content_type='application/json')

@login_required
def api_transaction_stats(request):
    # Transaction statistics for the last 7 days
    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)
    
    stats = Transaction.objects.filter(
        date__range=[start_date, end_date]
    ).extra(
        {'date_only': "date(date)"}
    ).values('date_only', 'transaction_type').annotate(
        count=Count('id'),
        total_quantity=Sum('quantity')
    ).order_by('date_only')
    
    return HttpResponse(json.dumps(list(stats), default=str), content_type='application/json')

@login_required
def api_low_stock_products(request):
    low_stock_products = Product.objects.filter(
        stock_quantity__lte=F('min_stock')
    ).values('id', 'name', 'stock_quantity', 'min_stock', 'warehouse__name')
    
    return HttpResponse(json.dumps(list(low_stock_products), default=str), content_type='application/json')



# Export functions
@login_required
def export_report_excel(request, pk):
    report = get_object_or_404(Report, pk=pk)
    transactions = Transaction.objects.filter(date__gte=report.start_date, date__lte=report.end_date)
    
    data = {
        'Sana': [t.date.strftime('%Y-%m-%d %H:%M') for t in transactions],
        'Mahsulot': [t.product.name for t in transactions],
        'Turi': [t.get_transaction_type_display() for t in transactions],
        'Miqdor': [t.quantity for t in transactions],
        'Narx': [float(t.product.price) if t.product.price else 0 for t in transactions],
        'Umumiy Summa': [float(t.quantity * (t.product.price if t.product.price else 0)) for t in transactions],
        'Foydalanuvchi': [t.user.username for t in transactions],
        'Izoh': [t.description for t in transactions],
    }
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    filename = f"{report.report_type}_report_{report.generated_at.strftime('%Y%m%d_%H%M')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    df.to_excel(response, index=False)
    
    UserLog.objects.create(user=request.user, action=f"Hisobotni eksport qildi: {report}")
    return response

# Qo'shimcha view funksiyalari
@login_required
def warehouse_detail(request, pk):
    warehouse = get_object_or_404(Warehouse, pk=pk)
    products = Product.objects.filter(warehouse=warehouse)
    low_stock = products.filter(stock_quantity__lte=F('min_stock'))
    
    context = {
        'warehouse': warehouse,
        'products': products,
        'low_stock': low_stock,
    }
    return render(request, 'inventor/warehouse_detail.html', context)

@login_required
@admin_required
def warehouse_create(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save()
            UserLog.objects.create(user=request.user, action=f"Yangi ombor yaratdi: {warehouse.name}")
            messages.success(request, "Ombor muvaffaqiyatli yaratildi!")
            return redirect('inventor:warehouse_list')
    else:
        form = WarehouseForm()
    return render(request, 'inventor/warehouse_form.html', {'form': form})

@login_required
def debt_list(request):
    debts = Debt.objects.all().order_by('-debt_date')
    return render(request, 'inventor/debt_list.html', {'debts': debts})

@login_required
def dashboard_statistics(request):
    # Dashboard statistikasi
    total_warehouses = Warehouse.objects.count()
    total_products = Product.objects.count()
    total_transactions = Transaction.objects.count()
    total_revenue = Transaction.objects.filter(
        transaction_type='OUT_SALE'
    ).aggregate(
        total=Sum(F('quantity') * F('product__price'))
    )['total'] or 0
    
    context = {
        'total_warehouses': total_warehouses,
        'total_products': total_products,
        'total_transactions': total_transactions,
        'total_revenue': total_revenue,
    }
    return render(request, 'inventor/dashboard_stats.html', context)