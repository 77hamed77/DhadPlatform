# DhadPlatform/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView 

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('registration.urls')),

    # مسارات المصادقة
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # مسارات تطبيق academic (لصفحات المواد والدروس)
    path('', include('academic.urls')),
    
    path('contacts/', include('contacts.urls', namespace='contacts')), 
    
    
    path('', include('messaging.urls')), 
    
    # لوحة التحكم الخاصة بالإدارة
    path('admin-dashboard/', include('dashboard.urls')), 
]

handler404 = TemplateView.as_view(template_name='404.html')