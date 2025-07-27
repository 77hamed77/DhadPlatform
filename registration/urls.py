from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_request, name='register_request'), # مسار لصفحة نموذج التسجيل
    path('register/success/', views.registration_success, name='registration_success'), # مسار لصفحة التأكيد
]