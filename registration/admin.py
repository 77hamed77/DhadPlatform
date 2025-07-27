# registration/admin.py
from django.contrib import admin
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from .models import RegistrationRequest
from core.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags, format_html

class RegistrationRequestAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'email', 'whatsapp_number', 'preferred_payment_method', 'status', 'created_at', 'approved_at', 'user_link' # <--- إضافة preferred_payment_method
    )
    search_fields = (
        'full_name', 'email', 'whatsapp_number', 'country'
    )
    list_filter = (
        'status', 'gender', 'study_level', 'country', 'program', 'preferred_payment_method' # <--- إضافة preferred_payment_method
    )

    fieldsets = (
        (None, {
            'fields': ('full_name', 'date_of_birth', 'gender')
        }),
        ('معلومات الاتصال', {
            'fields': ('email', 'whatsapp_number', 'preferred_payment_method') # <--- إضافة preferred_payment_method هنا
        }),
        ('المعلومات الجغرافية', {
            'fields': ('country', 'current_location')
        }),
        ('المعلومات الدراسية', {
            'fields': ('study_level', 'curriculum', 'program', 'grade', 'arabic_level', 'native_language')
        }),
        ('حالة الطلب', {
            'fields': ('status', 'created_at', 'approved_at', 'user')
        }),
    )
    readonly_fields = ('created_at', 'approved_at', 'user')

    def user_link(self, obj):
        if obj.user:
            return format_html('<a href="/admin/core/user/{}/change/">{}</a>', obj.user.pk, obj.user.username)
        return "-"
    user_link.short_description = 'المستخدم المرتبط'

    @admin.action(description='الموافقة على الطلبات وإنشاء حسابات للطلاب')
    def approve_and_create_students(self, request, queryset):
        approved_count = 0
        already_approved_count = 0
        failed_count = 0

        for req in queryset:
            if req.status == 'approved':
                already_approved_count += 1
                messages.warning(request, f'طلب التسجيل من {req.full_name} ({req.email}) تمت الموافقة عليه مسبقاً.')
                continue

            if req.status == 'pending':
                try:
                    if User.objects.filter(email=req.email).exists():
                        messages.error(request, f'فشل إنشاء حساب للطالب {req.full_name}: يوجد مستخدم بالفعل بهذا البريد الإلكتروني ({req.email}).')
                        failed_count += 1
                        continue

                    user = User(
                        username=req.email,
                        email=req.email,
                        role='student',
                        is_active=True,
                        first_name=req.full_name.split(' ')[0] if req.full_name else '',
                        last_name=' '.join(req.full_name.split(' ')[1:]) if req.full_name and len(req.full_name.split(' ')) > 1 else '',
                        phone_number=req.whatsapp_number,
                        country=req.country,
                    )
                    user.password = req.password_hash
                    user.save()

                    req.status = 'approved'
                    req.approved_at = timezone.now()
                    req.user = user
                    req.save()

                    subject = 'تمت الموافقة على طلب تسجيلك في منصة ضاد التعليمية!'
                    
                    html_message = render_to_string('registration/approved_student_email.html', {
                        'student_name': req.full_name,
                        'email': req.email,
                        'login_link': request.build_absolute_uri('/login/')
                    })
                    plain_message = strip_tags(html_message)

                    from_email = settings.DEFAULT_FROM_EMAIL
                    recipient_list = [req.email]

                    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message, fail_silently=False)
                    
                    messages.success(request, f'تمت الموافقة على طلب {req.full_name} وتم إنشاء حسابه بنجاح. تم إرسال إشعار عبر البريد الإلكتروني.')
                    approved_count += 1

                except Exception as e:
                    messages.error(request, f'فشل معالجة طلب {req.full_name} ({req.email}): {e}')
                    failed_count += 1
            else:
                messages.warning(request, f'طلب التسجيل من {req.full_name} ليس "قيد الانتظار" ({req.status}).')
        
        if approved_count > 0:
            self.message_user(request, f'تمت الموافقة على {approved_count} طلب تسجيل وإنشاء حسابات.', level=messages.SUCCESS)
        if already_approved_count > 0:
            self.message_user(request, f'تم تجاهل {already_approved_count} طلب لأنه تمت الموافقة عليه مسبقاً.', level=messages.INFO)
        if failed_count > 0:
            self.message_user(request, f'فشل معالجة {failed_count} طلب.', level=messages.ERROR)
        
        if approved_count == 0 and already_approved_count == 0 and failed_count == 0:
            self.message_user(request, 'لا توجد طلبات معلقة قابلة للمعالجة.', level=messages.WARNING)

    actions = [approve_and_create_students]

admin.site.register(RegistrationRequest, RegistrationRequestAdmin)