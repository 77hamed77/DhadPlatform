# dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard' # يمكن أن يكون لديك app_name هنا

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('user-data-api/', views.user_data_api, name='user_data_api'),
    path('approve-request/<int:request_id>/', views.approve_registration_request, name='approve_registration_request'),
    path('reject-request/<int:request_id>/', views.reject_registration_request, name='reject_registration_request'),
    # المسار الجديد لتوليد كلمة مرور عشوائية
    path('generate-password/', views.generate_random_password_api, name='generate_random_password_api'),
]