from django import forms
from .models import Message

class ContactForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'الاسم الكامل'}),
            'email': forms.EmailInput(attrs={'placeholder': 'البريد الإلكتروني'}),
            'subject': forms.TextInput(attrs={'placeholder': 'موضوع الرسالة'}),
            'message': forms.Textarea(attrs={'placeholder': 'اكتب رسالتك هنا...', 'rows': 5}),
        }
        labels = {
            'name': 'الاسم الكامل',
            'email': 'البريد الإلكتروني',
            'subject': 'الموضوع',
            'message': 'الرسالة',
        }