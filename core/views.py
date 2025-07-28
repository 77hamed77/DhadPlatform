# core/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash # لتحديث الجلسة بعد تغيير كلمة المرور
from django.http import Http404

# استيراد الفورمز (تأكد من أن هذه الفورمز معرفة في ملف forms.py الخاص بنفس التطبيق)
from .forms import ProfileEditForm, CustomPasswordChangeForm
from .models import User 

# استيراد النماذج من تطبيق academic
# نستخدم apps.get_model لضمان عدم وجود استيراد دائري إذا لزم الأمر
from django.apps import apps 

# الدالة الخاصة بالصفحة الرئيسية
def index(request):
    return render(request, 'core/index.html')

# الدالة الخاصة بلوحة التحكم (Dashboard)
@login_required
def dashboard(request):
    user_programs_and_courses = []
    upcoming_classes = []
    overall_progress_percentage = 0 

    show_activation_message = False
    if request.user.role == 'student':
        user_programs_and_courses = request.user.get_enrolled_programs()
        upcoming_classes = request.user.get_upcoming_classes()
        overall_progress_percentage = request.user.get_overall_progress_percentage() 

        if not request.user.is_active and request.user.determined_arabic_level != 'unassigned':
            show_activation_message = True

    context = {
        'user': request.user,
        'message': 'مرحباً بك في لوحة تحكم الطالب الخاصة بك!',
        'user_programs_and_courses': user_programs_and_courses,
        'upcoming_classes': upcoming_classes,
        'show_activation_message': show_activation_message, 
        'overall_progress_percentage': overall_progress_percentage, 
    }
    return render(request, 'core/dashboard.html', context)

# الدالة الخاصة بعرض وتعديل الملف الشخصي
@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تحديث ملفك الشخصي بنجاح!')
            return redirect('profile_view')
        else:
            messages.error(request, 'حدث خطأ في تحديث الملف الشخصي. يرجى مراجعة البيانات المدخلة.')
    else:
        form = ProfileEditForm(instance=request.user)

    context = {
        'form': form,
        'is_password_change': False 
    }
    return render(request, 'core/profile.html', context)

# الدالة الخاصة بتغيير كلمة المرور
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user) 
            messages.success(request, 'تم تغيير كلمة المرور بنجاح!')
            return redirect('profile_view') 
        else:
            messages.error(request, 'فشل تغيير كلمة المرور. يرجى مراجعة الأخطاء أدناه.')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    context = {
        'form': form,
        'is_password_change': True 
    }
    return render(request, 'core/profile.html', context)

# --------------------------------------------------------------------------
# دالة العرض الجديدة والمحسّنة لصفحة تفاصيل التقدم
# --------------------------------------------------------------------------
@login_required
def progress_detail(request):
    if request.user.role != 'student':
        messages.error(request, "لا تملك صلاحية الوصول إلى هذه الصفحة.")
        return redirect('core:dashboard')

    overall_progress_percentage = request.user.get_overall_progress_percentage()

    # جلب النماذج المطلوبة ديناميكياً لتجنب الاستيراد الدائري
    Course = apps.get_model('academic', 'Course')
    Lesson = apps.get_model('academic', 'Lesson')
    LessonProgress = apps.get_model('academic', 'LessonProgress')
    Test = apps.get_model('academic', 'Test')
    TestResult = apps.get_model('academic', 'TestResult')

    # 1. تفاصيل تقدم الدروس:
    # الحصول على جميع المواد التي سجل فيها الطالب
    enrolled_courses = request.user.get_enrolled_courses()
    
    courses_progress_data = []
    # متغير جديد لتخزين توصية الدورة الواحدة (إذا وجدت)
    course_recommendation = None 
    
    for course in enrolled_courses:
        total_lessons_in_course = Lesson.objects.filter(course=course).count()
        completed_lessons_in_course = LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course,
            is_completed=True
        ).count()
        
        # قائمة بالدروس المكتملة وغير المكتملة
        lessons_data = []
        # افترض أن لديك حقل 'order' في نموذج الدرس لفرزها
        all_lessons_in_course = Lesson.objects.filter(course=course).order_by('order') 
        for lesson in all_lessons_in_course:
            is_completed = LessonProgress.objects.filter(
                student=request.user,
                lesson=lesson,
                is_completed=True
            ).exists()
            lessons_data.append({
                'lesson': lesson,
                'is_completed': is_completed
            })

        course_completion_percentage = 0
        if total_lessons_in_course > 0:
            course_completion_percentage = (completed_lessons_in_course / total_lessons_in_course) * 100
        
        current_course_data = {
            'course': course,
            'total_lessons': total_lessons_in_course,
            'completed_lessons': completed_lessons_in_course,
            'completion_percentage': round(course_completion_percentage, 2),
            'lessons_data': lessons_data, # تفاصيل كل درس
        }
        courses_progress_data.append(current_course_data)

        # المنطق الجديد: البحث عن توصية واحدة للدورة في Python
        # إذا لم نجد توصية بعد، ونسبة إكمال هذه المادة أقل من 50% ولديها دروس
        if course_recommendation is None and \
           current_course_data['completion_percentage'] < 50 and \
           current_course_data['total_lessons'] > 0:
            course_recommendation = current_course_data
            # لا نستخدم break هنا لأننا قد نحتاج إلى 'courses_progress_data' الكاملة لأغراض أخرى
            # ولكننا نضمن أن 'course_recommendation' سيحمل الدورة الأولى فقط التي تستوفي الشرط

    # 2. تفاصيل نتائج الاختبارات:
    # تم تصحيح هذا السطر لاستخدام 'start_time' بدلاً من 'date_taken'
    student_test_results = TestResult.objects.filter(student=request.user).order_by('-start_time') # أحدث النتائج أولاً

    context = {
        'overall_progress_percentage': overall_progress_percentage,
        'courses_progress_data': courses_progress_data, # بيانات تقدم الدروس لكل مادة
        'student_test_results': student_test_results,    # نتائج الاختبارات
        'course_recommendation': course_recommendation, # التوصية الوحيدة للدورة
    }
    return render(request, 'core/progress_detail.html', context)


@login_required
def account_settings_view(request):
    """
    يعرض صفحة إعدادات الحساب التي يمكن أن تتضمن روابط لـ:
    - تعديل الملف الشخصي
    - تغيير كلمة المرور
    - إعدادات الإشعارات (إذا كانت موجودة)
    - إلخ.
    """
    context = {
        'current_page': 'account_settings' # لتحديد العنصر النشط في القائمة الجانبية أو التنقل
    }
    return render(request, 'core/account_settings.html', context)


# دالة اختبار لصفحة 404 (لأغراض التطوير فقط)
def test_404_view(request):
    raise Http404("هذه صفحة اختبار 404. تم الوصول إليها عبر مسار مخصص.")


def about_platform(request):
    return render(request, 'core/about_platform.html')