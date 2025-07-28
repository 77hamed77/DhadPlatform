# registration/forms.py
from django import forms
# from django.contrib.auth.hashers import make_password # لم نعد بحاجة إليها إذا أزلنا حقول كلمة المرور
from .models import RegistrationRequest

class RegistrationRequestForm(forms.ModelForm):
    # تم إزالة حقلي 'password' و 'password_confirm' من هنا لأن النموذج أصبح لـ "رغبة بالانضمام" فقط
    # ولن يطلب من المستخدم إدخال كلمة مرور مباشرة في هذه المرحلة.

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
            'preferred_payment_method',
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
            'preferred_payment_method': forms.Select(attrs={'class': 'form-select'}),
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
            'preferred_payment_method': 'طريقة الدفع المفضلة',
        }

    def clean(self):
        cleaned_data = super().clean()
        # تم إزالة التحقق من 'password' و 'password_confirm'
        
        whatsapp_number = cleaned_data.get('whatsapp_number')

        if whatsapp_number:
            cleaned_whatsapp = whatsapp_number.replace(' ', '').replace('-', '')
            if not cleaned_whatsapp.isdigit():
                self.add_error('whatsapp_number', "رقم الواتساب يجب أن يحتوي على أرقام فقط (بدون مسافات أو رموز).")
            cleaned_data['whatsapp_number'] = cleaned_whatsapp

        return cleaned_data
    
    def save(self, commit=True):
        # لم نعد بحاجة لتعيين password_hash هنا لأن حقول كلمة المرور قد أزيلت
        registration_request = super().save(commit=False)
        
        # إذا كنت تريد تعيين كلمة مرور افتراضية أو تركها فارغة ليتم تعيينها لاحقًا
        # على سبيل المثال، يمكنك تركها فارغة هنا، ثم يتم التعامل معها في الـ view
        # أو عند الموافقة على الطلب في لوحة التحكم.
        # تأكد أن حقل password_hash في موديل RegistrationRequest يسمح بالقيمة الفارغة (nullable).
        # مثال: registration_request.password_hash = "" أو None

        if commit:
            registration_request.save()
        return registration_request