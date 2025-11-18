# products/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Product, Category
from inventor.models import Warehouse, Supplier, Transaction
from users.decorators import warehouse_manager_required, admin_required, seller_required
from users.models import UserLog
from django.db.models import Q, Count, Sum, F
import pandas as pd
from django.http import HttpResponse
from django.utils import timezone

@login_required
def product_list(request):
    query = request.GET.get('q')
    products = Product.objects.all()
    
    # Role-based filtering
    try:
        role = request.user.userrole.role
        warehouse = request.user.userrole.warehouse
        if role == 'WAREHOUSE_MANAGER':
            products = products.filter(warehouse=warehouse)
        elif role == 'SELLER':
            products = products.filter(warehouse=warehouse)
    except:
        pass
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
            # Q(barcode__icontains=query)
        )
    
    products_with_low_stock = [product for product in products if product.is_low_stock()]
    
    UserLog.objects.create(user=request.user, action="Mahsulotlar ro'yxatini ko'rdi")
    return render(request, 'products/product_list.html', {
        'products': products,
        'low_stock': products_with_low_stock,
        'query': query
    })

@login_required
@warehouse_manager_required
def product_create(request):
    # warehouses = Warehouse.objects.all()
    warehouses = request.user.userrole.warehouse
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        # barcode = request.POST.get('barcode')
        description = request.POST.get('description', '')
        price = request.POST.get('price')
        min_stock = request.POST.get('min_stock', 0)
        stock_quantity = request.POST.get('stock_quantity', 0)
        unit = request.POST.get('unit', 'piece')
        warehouse_id = request.POST.get('warehouse')
        supplier_id = request.POST.get('supplier')
        image = request.FILES.get('image')
        
        category = get_object_or_404(Category, id=category_id)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id) if warehouse_id else None
        supplier = get_object_or_404(Supplier, id=supplier_id) if supplier_id else None
        
        product = Product.objects.create(
            name=name,
            category=category,
            # barcode=barcode,
            description=description,
            price=price,
            min_stock=min_stock,
            stock_quantity=stock_quantity,
            unit=unit,
            warehouse=warehouse,
            supplier=supplier,
            image=image
        )
        
        UserLog.objects.create(user=request.user, action=f"Yangi mahsulot yaratdi: {name}")
        messages.success(request, "Mahsulot muvaffaqiyatli qo'shildi!")
        return redirect('products:product_list')
    
    return render(request, 'products/product_create.html', {
        'categories': categories,
        'warehouses': warehouses,
        'suppliers': suppliers
    })

@login_required
@warehouse_manager_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    warehouses = Warehouse.objects.all()
    categories = Category.objects.all()
    suppliers = Supplier.objects.all()
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.category_id = request.POST.get('category')
        # product.barcode = request.POST.get('barcode')
        product.description = request.POST.get('description', '')
        product.price = request.POST.get('price')
        product.min_stock = request.POST.get('min_stock', 0)
        product.stock_quantity = request.POST.get('stock_quantity', 0)
        product.unit = request.POST.get('unit', 'piece')
        product.warehouse_id = request.POST.get('warehouse')
        product.supplier_id = request.POST.get('supplier')
        
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        
        product.save()
        
        UserLog.objects.create(user=request.user, action=f"Mahsulotni tahrirladi: {product.name}")
        messages.success(request, "Mahsulot muvaffaqiyatli tahrirlandi!")
        return redirect('products:product_list')
    
    return render(request, 'products/product_edit.html', {
        'product': product,
        'categories': categories,
        'warehouses': warehouses,
        'suppliers': suppliers
    })

@login_required
@warehouse_manager_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product_name = product.name
    product.delete()
    
    UserLog.objects.create(user=request.user, action=f"Mahsulotni o'chirdi: {product_name}")
    messages.success(request, "Mahsulot muvaffaqiyatli o'chirildi!")
    return redirect('products:product_list')

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    transactions = Transaction.objects.filter(product=product).order_by('-date')[:10]
    
    context = {
        'product': product,
        'transactions': transactions,
    }
    return render(request, 'products/product_detail.html', context)

@login_required
@warehouse_manager_required
def category_list(request):
    categories = Category.objects.all().annotate(
        product_count=Count('products')
    )
    return render(request, 'products/category_list.html', {'categories': categories})

@login_required
@warehouse_manager_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        category = Category.objects.create(
            name=name,
            description=description
        )
        
        UserLog.objects.create(user=request.user, action=f"Yangi kategoriya yaratdi: {name}")
        messages.success(request, "Kategoriya muvaffaqiyatli yaratildi!")
        return redirect('products:category_list')
    
    return render(request, 'products/category_form.html')

@login_required
@warehouse_manager_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description', '')
        category.save()
        
        UserLog.objects.create(user=request.user, action=f"Kategoriyani tahrirladi: {category.name}")
        messages.success(request, "Kategoriya muvaffaqiyatli tahrirlandi!")
        return redirect('products:category_list')
    
    return render(request, 'products/category_form.html', {'category': category})

@login_required
@warehouse_manager_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    category_name = category.name
    category.delete()
    
    UserLog.objects.create(user=request.user, action=f"Kategoriyani o'chirdi: {category_name}")
    messages.success(request, "Kategoriya muvaffaqiyatli o'chirildi!")
    return redirect('products:category_list')

@login_required
def product_search(request):
    query = request.GET.get('q', '')
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            # Q(barcode__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    return render(request, 'products/product_search.html', {
        'products': products,
        'query': query
    })

@login_required
def low_stock_products(request):
    products = Product.objects.all()

    try:
        role = request.user.userrole.role
        warehouse = request.user.userrole.warehouse
        if role == 'WAREHOUSE_MANAGER':
            products = products.filter(warehouse=warehouse, stock_quantity__lte=F('min_stock'))
        elif role == 'SELLER':
            products = products.filter(warehouse=warehouse, stock_quantity__gt=0)
    except:
        pass
    return render(request, 'products/low_stock.html', {'products': products})

@login_required
def top_selling_products(request):
    # Get top selling products based on transaction history
    top_products = Transaction.objects.filter(
        transaction_type='OUT_SALE',
        date__gte=timezone.now() - timezone.timedelta(days=30)
    ).values(
        'product__name', 'product__category__name'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('product__price'))
    ).order_by('-total_sold')[:10]
    
    return render(request, 'products/top_selling.html', {'top_products': top_products})

@login_required
@warehouse_manager_required
def export_products(request):
    products = Product.objects.all()
    
    # Role-based filtering for export
    try:
        role = request.user.userrole.role
        warehouse = request.user.userrole.warehouse
        if role == 'WAREHOUSE_MANAGER':
            products = products.filter(warehouse=warehouse)
    except:
        pass
    
    data = {
        'Nomi': [p.name for p in products],
        'Kategoriya': [p.category.name for p in products],
        # 'Shtrix-kod': [p.barcode for p in products],
        'Tavsif': [p.description for p in products],
        'Narxi': [float(p.price) if p.price else 0 for p in products],
        'Oʻlchov birligi': [p.get_unit_display() for p in products],
        'Minimal zaxira': [p.min_stock for p in products],
        'Zaxiradagi miqdor': [p.stock_quantity for p in products],
        'Ombor': [p.warehouse.name if p.warehouse else '' for p in products],
        'Yetkazib beruvchi': [p.supplier.name if p.supplier else '' for p in products],
    }
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="mahsulotlar.xlsx"'
    df.to_excel(response, index=False)
    
    UserLog.objects.create(user=request.user, action="Mahsulotlarni Excelga eksport qildi")
    return response

@login_required
@warehouse_manager_required
def import_products(request):
    if request.method == 'POST':
        file = request.FILES['file']
        df = pd.read_excel(file)
        
        imported_count = 0
        updated_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                category_name = row.get('Kategoriya', '')
                if category_name:
                    category, _ = Category.objects.get_or_create(name=category_name)
                else:
                    category = None
                
                warehouse_name = row.get('Ombor', '')
                warehouse = Warehouse.objects.filter(name=warehouse_name).first() if warehouse_name else None
                
                supplier_name = row.get('Yetkazib beruvchi', '')
                supplier = Supplier.objects.filter(name=supplier_name).first() if supplier_name else None
                
                product_name = row.get('Nomi', '').strip()
                if not product_name:
                    errors.append(f"{index+2}-qatorda mahsulot nomi kiritilmagan")
                    continue
                
                # Mahsulotni nomi va kategoriyasi bo'yicha topish
                # Agar bir xil nomdagi mahsulotlar bo'lsa, kategoriya bilan aniqlash
                product_query = Product.objects.filter(name=product_name)
                if category:
                    product_query = product_query.filter(category=category)
                
                if product_query.exists():
                    # Mavjud mahsulotni yangilash
                    product = product_query.first()
                    product.name = product_name
                    product.category = category
                    product.description = row.get('Tavsif', product.description)
                    product.price = row.get('Narxi', product.price)
                    product.min_stock = row.get('Minimal zaxira', product.min_stock)
                    product.stock_quantity = row.get('Zaxiradagi miqdor', product.stock_quantity)
                    product.warehouse = warehouse
                    product.supplier = supplier
                    
                    # Unit (oʻlchov birligi) ni yangilash
                    unit = row.get('Oʻlchov birligi', '')
                    if unit and unit in dict(Product.UNIT_CHOICES):
                        product.unit = unit
                    
                    product.save()
                    updated_count += 1
                else:
                    # Yangi mahsulot yaratish
                    unit = row.get('Oʻlchov birligi', 'piece')
                    if unit not in dict(Product.UNIT_CHOICES):
                        unit = 'piece'
                    
                    Product.objects.create(
                        name=product_name,
                        category=category,
                        description=row.get('Tavsif', ''),
                        price=row.get('Narxi', 0),
                        min_stock=row.get('Minimal zaxira', 0),
                        stock_quantity=row.get('Zaxiradagi miqdor', 0),
                        unit=unit,
                        warehouse=warehouse,
                        supplier=supplier
                    )
                    imported_count += 1
                    
            except Exception as e:
                errors.append(f"{index+2}-qatorda xatolik: {str(e)}")
                continue
        
        # Log yozish
        UserLog.objects.create(
            user=request.user, 
            action=f"Mahsulotlarni import qildi: {imported_count} yangi, {updated_count} yangilandi"
        )
        
        # Xabarlarni ko'rsatish
        if errors:
            messages.warning(request, f"Import jarayonida {len(errors)} ta xatolik yuz berdi")
            # Xatoliklarni sessionga saqlash yoki alohida ko'rsatish
            request.session['import_errors'] = errors
        else:
            messages.success(request, f"Mahsulotlar muvaffaqiyatli import qilindi! {imported_count} yangi, {updated_count} yangilandi")
        
        return redirect('products:product_list')
    
    # Xatoliklarni templatega uzatish
    import_errors = request.session.pop('import_errors', [])
    return render(request, 'products/import_products.html', {'import_errors': import_errors})


@login_required
def dashboard(request):
    # Get statistics for dashboard
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(stock_quantity__lte=F('min_stock')).count()
    total_categories = Category.objects.count()
    
    # Recent transactions
    recent_transactions = Transaction.objects.all().order_by('-date')[:5]
    
    context = {
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'total_categories': total_categories,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'products/dashboard.html', context)