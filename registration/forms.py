# registration/forms.py
from django import forms
from django.contrib.auth.hashers import make_password
from .models import RegistrationRequest

class RegistrationRequestForm(forms.ModelForm):
    password = forms.CharField(
        label="كلمة المرور",
        widget=forms.PasswordInput(attrs={'class': 'form-input'}),
        min_length=8,
        help_text="يجب أن تتكون كلمة المرور من 8 أحرف على الأقل."
    )
    password_confirm = forms.CharField(
        label="تأكيد كلمة المرور",
        widget=forms.PasswordInput(attrs={'class': 'form-input'})
    )

    class Meta:
        model = RegistrationRequest
        fields = [
            'full_name',
            'date_of_birth',
            'gender',
            'country',
            'current_location',
            'study_level',
            'curriculum',
            'program',
            'grade',
            'arabic_level',
            'native_language',
            'email',
            'whatsapp_number',
            'preferred_payment_method', # <--- إضافة هذا
            'password',
            'password_confirm'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'full_name': forms.TextInput(attrs={'class': 'form-input'}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
            'current_location': forms.TextInput(attrs={'class': 'form-input'}),
            'study_level': forms.TextInput(attrs={'class': 'form-input'}),
            'curriculum': forms.TextInput(attrs={'class': 'form-input'}),
            'program': forms.TextInput(attrs={'class': 'form-input'}),
            'grade': forms.TextInput(attrs={'class': 'form-input'}),
            'arabic_level': forms.TextInput(attrs={'class': 'form-input'}),
            'native_language': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-input'}),
            'preferred_payment_method': forms.Select(attrs={'class': 'form-select'}), # <--- إضافة هذا
        }
        labels = {
            'full_name': 'الاسم الكامل',
            'date_of_birth': 'تاريخ الميلاد',
            'gender': 'الجنس',
            'country': 'الدولة',
            'current_location': 'المكان الحالي',
            'study_level': 'المستوى الدراسي',
            'curriculum': 'منهاج الدراسة',
            'program': 'البرنامج',
            'grade': 'الصف',
            'arabic_level': 'مستوى اللغة العربية الحالي',
            'native_language': 'اللغة الأم',
            'email': 'البريد الإلكتروني',
            'whatsapp_number': 'رقم واتساب للتواصل (مع رمز الدولة)',
            'preferred_payment_method': 'طريقة الدفع المفضلة', # <--- إضافة هذا
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        whatsapp_number = cleaned_data.get('whatsapp_number')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "كلمة المرور وتأكيدها غير متطابقين.")
        
        if whatsapp_number:
            cleaned_whatsapp = whatsapp_number.replace(' ', '').replace('-', '')
            if not cleaned_whatsapp.isdigit():
                self.add_error('whatsapp_number', "رقم الواتساب يجب أن يحتوي على أرقام فقط (بدون مسافات أو رموز).")
            cleaned_data['whatsapp_number'] = cleaned_whatsapp

        return cleaned_data
    
    def save(self, commit=True):
        registration_request = super().save(commit=False)
        registration_request.password_hash = make_password(self.cleaned_data['password'])
        
        if commit:
            registration_request.save()
        return registration_request