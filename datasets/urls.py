from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    path('', views.dataset_list, name='dataset_list'),
    path('upload/', views.upload_dataset, name='upload'),
    path('<int:pk>/', views.dataset_detail, name='dataset_detail'),
    path('<int:pk>/import/', views.trigger_import, name='trigger_import'),
]
