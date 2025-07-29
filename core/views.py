# core/views.py

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash # لتحديث الجلسة بعد تغيير كلمة المرور
from django.http import Http404
from django.apps import apps # لاستخدام apps.get_model لضمان عدم وجود استيراد دائري

# استيراد الفورمز (تأكد من أن هذه الفورمز معرفة في ملف forms.py الخاص بنفس التطبيق)
from .forms import ProfileEditForm, CustomPasswordChangeForm
from .models import User 

# استيراد النماذج من تطبيق academic
# بما أننا نستخدمها في دوال عرض متعددة، سنقوم باستيرادها مباشرة لتجنب التكرار
# إذا كانت لديك مشكلة في الاستيراد الدائري بين core و academic،
# فاستخدم apps.get_model() داخل الدوال التي تحتاجها فقط.
# ولكن عادةً هذا لا يكون مشكلة إذا كان academic لا يستورد من core مباشرة في models.py
from academic.models import Program, Course, Class, Lesson, EducationalFile, Assignment, Submission, Test, TestResult, LessonProgress

# --------------------------------------------------------------------------
# دوال العرض العامة/الطلابية
# --------------------------------------------------------------------------

# الدالة الخاصة بالصفحة الرئيسية
def index(request):
    return render(request, 'core/index.html')

# الدالة الخاصة بلوحة التحكم (Dashboard) - للطالب
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
    elif request.user.role == 'teacher':
        # إذا كان المستخدم معلمًا، قم بتوجيهه إلى لوحة تحكم المعلم
        return redirect('core:teacher_dashboard')
    elif request.user.role == 'admin':
        # إذا كان المستخدم مديرًا، قم بتوجيهه إلى لوحة تحكم المدير (إذا كانت موجودة)
        return redirect('admin:index') # أو إلى لوحة تحكم مخصصة للمدير

    context = {
        'user': request.user,
        'message': 'مرحباً بك في لوحة تحكم الطالب الخاصة بك!' if request.user.role == 'student' else 'مرحباً بك!',
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
            return redirect('core:profile_view') # تأكد من استخدام اسم المسار الصحيح
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
            return redirect('core:profile_view') # تأكد من استخدام اسم المسار الصحيح
        else:
            messages.error(request, 'فشل تغيير كلمة المرور. يرجى مراجعة الأخطاء أدناه.')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    context = {
        'form': form,
        'is_password_change': True 
    }
    return render(request, 'core/profile.html', context)

# الدالة الجديدة والمحسّنة لصفحة تفاصيل التقدم
@login_required
def progress_detail(request):
    if request.user.role != 'student':
        messages.error(request, "لا تملك صلاحية الوصول إلى هذه الصفحة.")
        return redirect('core:dashboard') # أو حيث تريد توجيههم

    overall_completion_percentage = request.user.get_overall_progress_percentage() 

    # 1. تفاصيل تقدم الدروس:
    enrolled_courses = request.user.get_enrolled_courses()
    
    courses_progress_data = []
    first_course_recommendation = None 
    
    for course in enrolled_courses:
        total_lessons_in_course = Lesson.objects.filter(course=course).count()
        completed_lessons_in_course = LessonProgress.objects.filter(
            student=request.user,
            lesson__course=course,
            status='completed' 
        ).count()
        
        lessons_data = []
        try:
            # افتراض وجود حقل 'order' في نموذج الدرس. إذا لم يكن موجودًا، استخدم 'id'.
            all_lessons_in_course = Lesson.objects.filter(course=course).order_by('order') 
        except Exception: # Catch if 'order' field does not exist
             all_lessons_in_course = Lesson.objects.filter(course=course).order_by('id') 

        for lesson in all_lessons_in_course:
            is_completed = LessonProgress.objects.filter(
                student=request.user,
                lesson=lesson,
                status='completed' 
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
        if first_course_recommendation is None and \
           current_course_data['completion_percentage'] < 50 and \
           current_course_data['total_lessons'] > 0:
            first_course_recommendation = current_course_data
            
    # 2. تفاصيل نتائج الاختبارات:
    placement_test_result = None
    try:
        placement_test_result = TestResult.objects.filter(
            student=request.user, 
            test__title='اختبار تحديد المستوى' 
        ).order_by('-start_time').first() # أحدث نتيجة لاختبار تحديد المستوى
    except TestResult.DoesNotExist:
        pass 

    context = {
        'overall_completion_percentage': overall_completion_percentage,
        'courses_progress_data': courses_progress_data, 
        'placement_test_result': placement_test_result, 
        'first_course_recommendation': first_course_recommendation, 
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

# --------------------------------------------------------------------------
# دوال العرض الخاصة بالمعلم
# --------------------------------------------------------------------------

# دالة مساعدة للتحقق من أن المستخدم معلم
def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'

@login_required
@user_passes_test(is_teacher, login_url='/login/') # وجه المستخدمين غير المعلمين إلى صفحة تسجيل الدخول أو أخرى
def teacher_dashboard(request):
    # هنا سنقوم بجمع البيانات التي سيحتاجها المعلم
    # الدورات التي يدرسها المعلم الحالي
    teacher_courses = Course.objects.filter(classes__teacher=request.user).distinct().order_by('name')

    # الحلقات التي يديرها المعلم (المرتبطة مباشرة به)
    teacher_classes = Class.objects.filter(teacher=request.user).order_by('start_time')

    # الواجبات التي قام المعلم بإنشائها أو المتعلقة بدوراته
    # يجب أن تكون الواجبات مرتبطة بمساق تابع لدورة المعلم
    # أو، إذا كان الواجب يملك foreign key للمعلم، يمكن فلترته مباشرة
    # حاليا، نفترض أنها مرتبطة بالدورة التي يدرسها المعلم
    teacher_assignments = Assignment.objects.filter(course__in=teacher_courses).order_by('-due_date')

    # التسليمات التي لم يتم تصحيحها بعد في واجبات المعلم
    pending_submissions = Submission.objects.filter(
        assignment__in=teacher_assignments,
        status='pending'
    ).count()

    context = {
        'teacher_courses': teacher_courses,
        'teacher_classes': teacher_classes,
        'teacher_assignments': teacher_assignments,
        'pending_submissions': pending_submissions,
        'user': request.user, # لتمرير معلومات المستخدم إلى القالب
    }
    return render(request, 'core/teacher_dashboard.html', context)