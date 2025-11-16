# products/urls.py
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Asosiy mahsulot URL'lari
    path('', views.product_list, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Kategoriya URL'lari
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    
    # Qidiruv va filtrlash URL'lari
    path('search/', views.product_search, name='product_search'),
    
    # Import/Export URL'lari
    path('export/', views.export_products, name='export_products'),
    path('import/', views.import_products, name='import_products'),
    
    # Statistika va hisobot URL'lari
    path('statistics/low-stock/', views.low_stock_products, name='low_stock_products'),
    path('statistics/top-selling/', views.top_selling_products, name='top_selling_products'),
    
    # Dashboard va bosh sahifa
    path('dashboard/', views.dashboard, name='dashboard'),
]