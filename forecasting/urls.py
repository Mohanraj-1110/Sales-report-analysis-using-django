from django.urls import path
from . import views

app_name = 'forecasting'

urlpatterns = [
    path('', views.forecast_view, name='forecast'),
    path('train/', views.train_forecast, name='train'),
]
