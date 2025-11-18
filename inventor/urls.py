from django.urls import path
from . import views

app_name = 'inventor'

urlpatterns = [
    # Ombor URL'lari
    path('warehouses/', views.warehouse_list, name='warehouse_list'),
    path('warehouses/<int:pk>/', views.warehouse_detail, name='warehouse_detail'),
    path('warehouses/<int:pk>/stock/', views.warehouse_stock, name='warehouse_stock'),
    path('warehouses/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', views.warehouse_edit, name='warehouse_edit'),
    path('warehouses/<int:pk>/delete/', views.warehouse_delete, name='warehouse_delete'),
    
    # Tranzaksiya URL'lari
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/history/', views.transaction_history, name='transaction_history'),
    path('transactions/export/', views.export_transactions, name='export_transactions'),
    
    # Yetkazib beruvchilar URL'lari
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),
    path('suppliers/<int:pk>/products/', views.supplier_products, name='supplier_products'),
    path('suppliers/<int:pk>/stats/', views.supplier_stats, name='supplier_stats'),
    
    # Hisobotlar URL'lari
    path('reports/generate/', views.report_generate, name='report_generate'),
    path('reports/', views.report_list, name='report_list'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/export/', views.export_report_excel, name='export_report_excel'),
    
    # Sozlamalar URL'lari
    path('settings/', views.settings_update, name='settings_update'),
    path('settings/backup_database/', views.backup_database, name='backup_database'),
    path('backup/download-sql/', views.download_database_file, name='download_sql_backup'),
    path('settings/bulk-price-update/', views.bulk_price_update, name='bulk_price_update'),
    path('settings/backup/', views.backup_database, name='backup_database'),
    path('settings/restore/', views.restore_database, name='restore_database'),
    path('settings/export-products/', views.export_products, name='export_products'),
    path('settings/import-products/', views.import_products, name='import_products'),
    
    # Qarzdorlik URL'lari
    path('debts/', views.debt_list, name='debt_list'),
    path('debts/<int:pk>/pay/', views.debt_payment, name='debt_payment'),
    path('debts/export/', views.export_debts, name='export_debts'),
    
    # Statistika URL'lari
    path('statistics/dashboard/', views.dashboard_statistics, name='dashboard_statistics'),
    path('statistics/sales/', views.sales_statistics, name='sales_statistics'),
    path('statistics/inventory/', views.inventory_statistics, name='inventory_statistics'),
    
    # API va AJAX URL'lari
    path('api/warehouse-stock/<int:pk>/', views.api_warehouse_stock, name='api_warehouse_stock'),
    path('api/transaction-stats/', views.api_transaction_stats, name='api_transaction_stats'),
    path('api/low-stock-products/', views.api_low_stock_products, name='api_low_stock_products'),
]