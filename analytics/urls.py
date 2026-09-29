from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('sales/', views.sales_analytics, name='sales'),
    path('categories/', views.category_analytics, name='categories'),
    path('geography/', views.geography_analytics, name='geography'),
    path('api/revenue-trends/', views.api_revenue_trends, name='api_revenue_trends'),
    path('api/category-distribution/', views.api_category_distribution, name='api_category_distribution'),
]
