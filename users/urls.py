from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Auth
    path('users/login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    
    # Admin
    path('admin1/dashboard1/', views.admin_dashboard, name='admin_dashboard'),
    path('admin1/create-warehouse-manager/', views.create_warehouse_manager, name='create_warehouse_manager'),
    path('admin1/payments/', views.payment_management, name='payment_management'),
    
    # Ombor xo'jayini
    path('warehouse-manager/dashboard/', views.warehouse_manager_dashboard, name='warehouse_manager_dashboard'),
    path('warehouse-manager/create-seller/', views.create_seller, name='create_seller'),
    path('warehouse-manager/seller/<int:seller_id>/stats/', views.seller_statistics, name='seller_statistics'),
    path('warehouse-manager/payment_management/', views.payment_management, name='make_payment'),
    
    # Sotuvchi
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('seller/take-product/<int:product_id>/', views.take_product, name='take_product'),
    
    # Umumiy
    path('dashboard/', views.dashboard, name='dashboard'),
]