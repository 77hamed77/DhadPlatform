from django.urls import path
from . import views

urlpatterns = [
    path('messages/', views.inbox, name='inbox'),
    path('messages/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('messages/start/<int:other_user_id>/', views.start_or_get_conversation, name='start_or_get_conversation'), # مسار جديد
]