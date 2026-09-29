from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('dashboard:index')),
    path('dashboard/', include('dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('analytics/', include('analytics.urls')),
    path('sales/', include('sales.urls')),
    path('customers/', include('customers.urls')),
    path('products/', include('products.urls')),
    path('predictions/', include('predictions.urls')),
    path('forecasting/', include('forecasting.urls')),
    path('datasets/', include('datasets.urls')),
    path('reports/', include('reports.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
