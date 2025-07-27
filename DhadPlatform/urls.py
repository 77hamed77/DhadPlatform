from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView  # تم استيراد TemplateView هنا

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('registration.urls')),

    # مسارات المصادقة
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # مسارات تطبيق academic (لصفحات المواد والدروس)
    path('', include('academic.urls')),
    
    # تم إضافة namespace='contacts' هنا
    path('contacts/', include('contacts.urls', namespace='contacts')), 
    
    # مسارات تطبيق messaging (للرسائل)
    path('', include('messaging.urls')), 
]


# تعريف الـ handler404
# هذا سيجعل Django يستخدم 404.html عندما لا يجد مسارًا
handler404 = TemplateView.as_view(template_name='404.html')