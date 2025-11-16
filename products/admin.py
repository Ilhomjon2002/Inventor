from django.contrib import admin
from .models import Category, Product
# Register your models here.

# Admin sahifalarini ro'yxatdan o'tkazish
admin.site.register(Category)
admin.site.register(Product)