# core/urls.py
from django.urls import path
from . import views # Import your views from the current app
# from django.contrib.auth import views as auth_views # You were importing this before, but you now have your own change_password_view

app_name = 'core' # IMPORTANT: Ensure this is defined if you use 'core:change_password'

urlpatterns = [
    path('', views.index, name='index'), # Your existing index view
    path('dashboard/', views.dashboard, name='dashboard'), # Your existing dashboard view
    path('profile/', views.profile_view, name='profile'), # Your existing profile view
    
    # This is the line that was likely missing or incorrect
    path('password-change/', views.change_password_view, name='change_password'),
    
    # You might also want a success URL after password change,
    # but for now, redirecting back to profile_view is handled in change_password_view.
    # If you want a dedicated 'password_change_done' page, you'd add:
    # path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='core/password_change_done.html'), name='password_change_done'),

    # Add other core URLs as needed, e.g., for account settings
    path('account-settings/', views.account_settings_view, name='account_settings'),
    path('test-404/', views.test_404_view, name='test_404'),
    path('about-platform/', views.about_platform, name='about_platform'),
]