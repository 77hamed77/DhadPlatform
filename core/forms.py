from django import forms
from .models import User
from django.contrib.auth.forms import PasswordChangeForm


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        # أضف 'profile_picture' هنا
        fields = ['first_name', 'last_name', 'phone_number', 'country', 'profile_picture']
        labels = {
            'first_name': 'الاسم الأول',
            'last_name': 'الاسم الأخير',
            'phone_number': 'رقم الواتساب',
            'country': 'الدولة',
            'profile_picture': 'الصورة الشخصية', # تسمية للحقل الجديد
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
            # إضافة widget خاص لحقل الصورة لتخصيص مظهره
            'profile_picture': forms.FileInput(attrs={'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none'})
        }

# ... (CustomPasswordChangeForm كما هي) ...
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # إضافة كلاسات Tailwind لجميع الحقول
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})
        # تخصيص التسميات باللغة العربية
        self.fields['old_password'].label = 'كلمة المرور الحالية'
        self.fields['new_password1'].label = 'كلمة المرور الجديدة'
        self.fields['new_password2'].label = 'تأكيد كلمة المرور الجديدة'