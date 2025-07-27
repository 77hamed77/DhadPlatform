# core/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash # لتحديث الجلسة بعد تغيير كلمة المرور
from django.http import Http404 # لاستخدامها في test_404_view

# استيراد الفورمز (تأكد من أن هذه الفورمز معرفة في ملف forms.py الخاص بنفس التطبيق)
from .forms import ProfileEditForm, CustomPasswordChangeForm

# الدالة الخاصة بالصفحة الرئيسية
def index(request):
    return render(request, 'core/index.html')

# الدالة الخاصة بلوحة التحكم (Dashboard)
@login_required
def dashboard(request):
    user_programs_and_courses = []
    upcoming_classes = []
    overall_progress_percentage = 0 # القيمة الافتراضية

    show_activation_message = False
    if request.user.role == 'student':
        user_programs_and_courses = request.user.get_enrolled_programs()
        upcoming_classes = request.user.get_upcoming_classes()
        overall_progress_percentage = request.user.get_overall_progress_percentage() # جلب نسبة التقدم (تم دمجها من تعريف الـ dashboard الثاني)

        # رسالة خاصة إذا كان المستخدم غير نشط (مفعل) بعد اختبار تحديد المستوى
        if not request.user.is_active and request.user.determined_arabic_level != 'unassigned':
            show_activation_message = True
            # يمكن هنا إضافة رسالة تحذيرية لـ messages إذا أردت
            # messages.warning(request, 'حسابك قيد التجميد بانتظار توفر مقعد دراسي مناسب.')

    context = {
        'user': request.user,
        'message': 'مرحباً بك في لوحة تحكم الطالب الخاصة بك!',
        'user_programs_and_courses': user_programs_and_courses,
        'upcoming_classes': upcoming_classes,
        'show_activation_message': show_activation_message, # تمرير المتغير للقالب
        'overall_progress_percentage': overall_progress_percentage, # تمرير نسبة التقدم
    }
    return render(request, 'core/dashboard.html', context)

# الدالة الخاصة بعرض وتعديل الملف الشخصي
@login_required
def profile_view(request):
    if request.method == 'POST':
        # مهم: تمرير request.FILES إذا كان النموذج يحتوي على حقل ملف
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
        'is_password_change': False # للتأكيد أننا في قسم تعديل الملف الشخصي وليس تغيير كلمة المرور
    }
    return render(request, 'core/profile.html', context)

# الدالة الخاصة بتغيير كلمة المرور
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user) # مهم لتحديث جلسة المستخدم بعد تغيير كلمة المرور
            messages.success(request, 'تم تغيير كلمة المرور بنجاح!')
            return redirect('profile_view') # بعد تغيير كلمة المرور بنجاح، نعود لصفحة الملف الشخصي
        else:
            messages.error(request, 'فشل تغيير كلمة المرور. يرجى مراجعة الأخطاء أدناه.')
    else:
        form = CustomPasswordChangeForm(user=request.user)

    context = {
        'form': form,
        'is_password_change': True # لتمييز النموذج في القالب
    }
    return render(request, 'core/profile.html', context) # يمكن استخدام نفس القالب أو قالب منفصل

# **NEW: الدالة الخاصة بصفحة إعدادات الحساب**
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