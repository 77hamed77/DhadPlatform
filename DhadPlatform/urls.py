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
    
    # مسارات Django Authentication Views لإعادة تعيين كلمة المرور
    # هذه المسارات لم تعد ضرورية للطالب لتسجيل الدخول الأول،
    # لكن يمكن الإبقاء عليها إذا كنت تريدها كخيار مستقبلي لإعادة تعيين كلمة المرور.
    path('password_reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
]

handler404 = TemplateView.as_view(template_name='404.html')