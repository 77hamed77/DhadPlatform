from django.urls import path
from . import views

app_name = 'contacts' # تحديد اسم namespace للتطبيق

urlpatterns = [
    path('contact/', views.contact_view, name='contact'),
    path('contact/success/', views.contact_success_view, name='contact_success'),
]