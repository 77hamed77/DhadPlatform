from django.shortcuts import render, redirect # استيراد redirect
from django.contrib import messages # لاستخدام رسائل Django
from django.core.mail import send_mail # لاستخدام إرسال البريد الإلكتروني
from django.conf import settings # لاستيراد الإعدادات من settings.py
from django.template.loader import render_to_string # لإنشاء قوالب HTML للبريد الإلكتروني
from django.utils.html import strip_tags # لإزالة وسوم HTML من النص
from .forms import RegistrationRequestForm # استيراد النموذج الذي أنشأناه
from core.models import User # لاستيراد نموذج المستخدم الخاص بك للحصول على email المدراء
from .models import RegistrationRequest # تأكد من استيراد نموذج طلب التسجيل الفعلي

# واجهة (View) لمعالجة نموذج طلب التسجيل
def register_request(request):
    if request.method == 'POST':
        # إذا كان الطلب من نوع POST (أي أن المستخدم أرسل النموذج)
        form = RegistrationRequestForm(request.POST) # إنشاء النموذج ببيانات POST
        if form.is_valid():
            # إذا كانت البيانات المدخلة في النموذج صحيحة
            registration_request = form.save() # حفظ بيانات النموذج في قاعدة البيانات (ينشئ كائن RegistrationRequest جديد)
            
            messages.success(request, 'تم استلام طلب التسجيل الخاص بك بنجاح! سنتواصل معك قريباً.') # رسالة نجاح

            # -----------------------------------------------------------------
            # إشعار الإدارة بوجود طلب تسجيل جديد عبر البريد الإلكتروني
            # -----------------------------------------------------------------
            subject = 'طلب تسجيل جديد على منصة ضاد التعليمية'
            
            # إنشاء قالب HTML للبريد الإلكتروني
            html_message = render_to_string('registration/new_student_notification_email.html', {
                'username': registration_request.full_name, # افترض أن لديك حقل 'full_name' في RegistrationRequest
                'email': registration_request.email,
                'phone_number': registration_request.whatsapp_number, # **تم التعديل هنا: استخدام whatsapp_number**
                'country': registration_request.country,
                'registration_date': registration_request.created_at.strftime("%Y-%m-%d %H:%M:%S"), # **تم التعديل هنا: افتراض created_at**
                # رابط لطلب التسجيل في لوحة الإدارة
                'admin_link': request.build_absolute_uri(f'/admin/registration/registrationrequest/{registration_request.id}/change/') 
            })
            plain_message = strip_tags(html_message) # نص عادي للبريد الإلكتروني (للتوافق)

            # تحديد البريد الإلكتروني للمسؤولين
            # نبحث عن جميع المستخدمين الذين لديهم دور 'admin' وحساباتهم نشطة
            admin_emails = [admin.email for admin in User.objects.filter(role='admin', is_active=True) if admin.email]
            
            if admin_emails:
                try:
                    send_mail(
                        subject,
                        plain_message,
                        settings.DEFAULT_FROM_EMAIL, # البريد الإلكتروني المرسل منه (من settings.py)
                        admin_emails, # قائمة بعناوين البريد الإلكتروني للمستقبلين
                        html_message=html_message, # إرسال نسخة HTML من الرسالة
                        fail_silently=False, # إذا كان False، سيتم رفع استثناء عند الفشل
                    )
                    messages.info(request, "تم إرسال إشعار بالبريد الإلكتروني للمسؤولين.")
                except Exception as e:
                    # في حالة فشل الإرسال، نعرض رسالة خطأ للمستخدم ونقوم بتسجيل الخطأ (في بيئة الإنتاج)
                    messages.error(request, f"فشل إرسال إشعار البريد الإلكتروني للمسؤولين: {e}. يرجى التحقق من إعدادات البريد SMTP.")
                    # هنا يمكنك إضافة منطق تسجيل الخطأ إلى ملف سجلات (logging)
            else:
                messages.warning(request, "لم يتم العثور على عناوين بريد إلكتروني للمسؤولين لإرسال الإشعار. يرجى التأكد من وجود مستخدمين بدور 'admin' مع بريد إلكتروني صالح.")


            return redirect('registration_success') # إعادة توجيه المستخدم لصفحة تأكيد
        else:
            # إذا كانت البيانات غير صحيحة، نعرض رسائل الخطأ
            messages.error(request, 'حدث خطأ في بيانات النموذج. يرجى مراجعة الحقول.')
    else:
        # إذا كان الطلب من نوع GET (أي أن المستخدم يطلب الصفحة لأول مرة)
        form = RegistrationRequestForm() # إنشاء نموذج فارغ

    # عرض القالب مع النموذج
    return render(request, 'registration/register_request.html', {'form': form})

# واجهة (View) لصفحة التأكيد بعد التسجيل
def registration_success(request):
    return render(request, 'registration/registration_success.html')