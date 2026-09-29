from django.urls import path
from . import views

app_name = 'predictions'

urlpatterns = [
    path('repurchase/', views.repurchase_predictions, name='repurchase'),
    path('models/', views.model_registry, name='models'),
    path('retrain/', views.retrain_model, name='retrain'),
]
