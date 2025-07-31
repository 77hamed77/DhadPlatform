# C:\projectsDejango\DhadPlatform\contacts\views.py

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from .utils import COUNTRY_DATA # <-- لم نعد بحاجة لـ get_flag_url هنا

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم إرسال رسالتك بنجاح! سنقوم بالرد عليك قريباً.')
            return redirect('contacts:contact_success')
        else:
            messages.error(request, 'حدث خطأ أثناء إرسال رسالتك. يرجى مراجعة الحقول.')
    else:
        form = ContactForm()
    
    context = {
        'form': form,
        'country_data_for_js': COUNTRY_DATA, # تمرير بيانات الدول لـ JS
    }
    return render(request, 'contacts/contact.html', context)

def contact_success_view(request):
    return render(request, 'contacts/contact_success.html')