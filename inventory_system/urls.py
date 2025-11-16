from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # App URL'lari
    path('', include('users.urls')),
    path('products/', include('products.urls')),
    path('inventor/', include('inventor.urls')),
    
    # Bosh sahifa
    path('', RedirectView.as_view(pattern_name='users:dashboard'), name='home'),
]

# Debug rejimida media fayllarini ko'rsatish
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# 404 xatosi uchun handler
handler404 = 'users.views.handler404'
handler500 = 'users.views.handler500'