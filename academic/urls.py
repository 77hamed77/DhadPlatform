# academic/urls.py
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'academic'
urlpatterns = [
    # Paths for Courses, Assignments, and Lessons
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('assignment/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('lesson/<int:lesson_id>/mark_completed/', views.mark_lesson_as_completed, name='mark_lesson_as_completed'),

    # Paths for Tests and Test Results
    path('tests/', views.test_list, name='test_list'),
    path('tests/<int:test_id>/start/', views.start_test, name='start_test'),
    # FIXED: Changed 'submit_answers/' to 'submit/' to match the common pattern and expected template usage
    path('tests/submit/<int:test_result_id>/', views.submit_test, name='submit_test'),
    path('tests/results/<int:test_result_id>/', views.test_result_detail, name='test_result_detail'),
]

# Serve media files in development mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)