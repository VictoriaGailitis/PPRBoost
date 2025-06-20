from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('start_finetune/', views.start_finetune, name='start_finetune'),
    path('get_finetune_status/', views.get_finetune_status, name='get_finetune_status'),
    path('get_faq/', views.get_faq, name='get_faq'),
] 