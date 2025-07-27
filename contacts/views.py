from django.shortcuts import render, redirect
from django.contrib import messages # لإظهار رسائل للمستخدم
from django.core.mail import send_mail # لإرسال البريد الإلكتروني
from django.conf import settings # لاستخدام إعدادات البريد الإلكتروني
from .forms import ContactForm

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # حفظ الرسالة في قاعدة البيانات
            message_instance = form.save()
            
            # إرسال بريد إلكتروني (اختياري، ويعتمد على إعدادات البريد في settings.py)
            subject = f"رسالة جديدة من موقعك: {form.cleaned_data['subject']}"
            email_body = f"""
الاسم: {form.cleaned_data['name']}
البريد الإلكتروني: {form.cleaned_data['email']}
الموضوع: {form.cleaned_data['subject']}
الرسالة:
{form.cleaned_data['message']}
            """
            from_email = settings.DEFAULT_FROM_EMAIL # أو بريدك الخاص
            recipient_list = [settings.CONTACT_FORM_RECIPIENT_EMAIL] # البريد الذي ستصلك عليه الرسائل
            
            try:
                send_mail(subject, email_body, from_email, recipient_list, fail_silently=False)
                messages.success(request, 'تم إرسال رسالتك بنجاح! سنتواصل معك قريباً.')
            except Exception as e:
                messages.error(request, f'حدث خطأ أثناء إرسال البريد الإلكتروني: {e}. تم حفظ رسالتك.')
                # يمكنك تسجيل الخطأ هنا لغرض التصحيح
                print(f"Error sending email: {e}")

            return redirect('contact_success') # إعادة توجيه لصفحة نجاح (سننشئها قريباً)
    else:
        form = ContactForm() # إذا كان الطلب GET، اعرض نموذج فارغ
    
    return render(request, 'contacts/contact.html', {'form': form})

def contact_success_view(request):
    return render(request, 'contacts/contact_success.html')