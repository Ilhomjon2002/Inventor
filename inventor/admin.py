from .models import Warehouse, Supplier, Transaction, Report, Settings
from django.contrib import admin

admin.site.register(Warehouse)
admin.site.register(Supplier)
admin.site.register(Transaction)
admin.site.register(Report)
admin.site.register(Settings)