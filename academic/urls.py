from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),

    path('tests/', views.test_list, name='test_list'),
    path('tests/<int:test_id>/start/', views.start_test, name='start_test'),
    path('tests/<int:test_result_id>/submit_answers/', views.submit_test, name='submit_test'),

    # مسار جديد لتحديث تقدم الدرس
    path('lesson/<int:lesson_id>/mark_completed/', views.mark_lesson_as_completed, name='mark_lesson_as_completed'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)