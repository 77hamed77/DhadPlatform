# C:\projectsDejango\DhadPlatform\contacts\forms.py

from django import forms
from .models import Message
from .utils import validate_whatsapp_number, COUNTRY_CHOICES, get_country_data

class ContactForm(forms.ModelForm):
    # تم تعريف الحقول المخصصة مع الكلاسات الخاصة بها مباشرة هنا
    country_code = forms.ChoiceField(
        choices=COUNTRY_CHOICES,
        label="رمز الدولة",
        required=False,
        # تم تحديد الكلاس 'country-select' مباشرة في الـ widget
        widget=forms.Select(attrs={'class': 'country-select'}) 
    )

    whatsapp_number_local = forms.CharField(
        max_length=15,
        required=False,
        label="رقم الواتساب",
        help_text="الجزء المتبقي من رقم الواتساب بدون رمز الاتصال الدولي.",
        # تم تحديد الكلاس 'form-input' مباشرة في الـ widget
        widget=forms.TextInput(attrs={
            'placeholder': 'مثال: 949123456', 
            'class': 'form-input', 
            'dir': 'ltr'
        })
    )

    class Meta:
        model = Message
        fields = ['name', 'email', 'whatsapp_number', 'subject', 'message'] 
        
        # تم تحديد الكلاس 'form-input' لجميع الحقول الأخرى هنا
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'الاسم الكامل', 
                'class': 'form-input'
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'البريد الإلكتروني', 
                'class': 'form-input'
            }),
            'subject': forms.TextInput(attrs={
                'placeholder': 'موضوع الرسالة', 
                'class': 'form-input'
            }),
            'message': forms.Textarea(attrs={
                'placeholder': 'اكتب رسالتك هنا...', 
                'rows': 5, 
                'class': 'form-input'
            }),
        }
        
        labels = {
            'name': 'الاسم الكامل',
            'email': 'البريد الإلكتروني',
            'subject': 'الموضوع',
            'message': 'الرسالة',
        }

    # دالة التحقق من الصحة تبقى كما هي، فهي تعمل بشكل صحيح
    def clean(self):
        cleaned_data = super().clean()
        country_code = cleaned_data.get('country_code')
        whatsapp_number_local = cleaned_data.get('whatsapp_number_local')

        if whatsapp_number_local or (country_code and country_code != ''):
            if not country_code or country_code == '':
                self.add_error('country_code', "الرجاء اختيار رمز الدولة لرقم الواتساب.")
            
            if not whatsapp_number_local:
                self.add_error('whatsapp_number_local', "الرجاء إدخال الجزء المتبقي من رقم الواتساب.")
            
            if not self.errors: 
                country_data = get_country_data(country_code)
                
                if not country_data or not country_data.get('dial_code'):
                    self.add_error('country_code', "رمز الدولة المحدد غير صالح.")
                else:
                    full_whatsapp_number = f"{country_data['dial_code']}{whatsapp_number_local}"
                    
                    is_valid, message = validate_whatsapp_number(full_whatsapp_number, region=country_code)

                    if not is_valid:
                        self.add_error('whatsapp_number_local', message)
                    else:
                        cleaned_data['whatsapp_number'] = message 
        
        return cleaned_data