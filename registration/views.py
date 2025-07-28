# registration/views.py
from django.shortcuts import render, redirect 
from django.contrib import messages 
# from django.core.mail import send_mail # لم نعد بحاجة إليها
# from django.conf import settings # لم نعد بحاجة إليها
# from django.template.loader import render_to_string # لم نعد بحاجة إليها
# from django.utils.html import strip_tags # لم نعد بحاجة إليها
from .forms import RegistrationRequestForm 
# from core.models import User # لم نعد بحاجة إليها هنا
from .models import RegistrationRequest 

def register_request(request):
    if request.method == 'POST':
        form = RegistrationRequestForm(request.POST) 
        if form.is_valid():
            registration_request = form.save() 
            
            messages.success(request, 'تم استلام طلب التسجيل الخاص بك بنجاح! سنتواصل معك قريباً.') 

            # -----------------------------------------------------------------
            # تمت إزالة قسم إرسال إشعار البريد الإلكتروني للمسؤولين
            # -----------------------------------------------------------------
            
            return redirect('registration_success') 
        else:
            messages.error(request, 'حدث خطأ في بيانات النموذج. يرجى مراجعة الحقول.')
    else:
        form = RegistrationRequestForm() 

    return render(request, 'registration/register_request.html', {'form': form})

def registration_success(request):
    return render(request, 'registration/registration_success.html')