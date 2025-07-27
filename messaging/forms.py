from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content'] # الحقل الوحيد الذي سيدخله المستخدم في النموذج
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'اكتب رسالتك هنا...',
                'class': 'form-textarea' # سنضيف له ستايل Tailwind
            })
        }
        labels = {
            'content': '' # لا نريد تسمية للحقل في الواجهة، فقط Placeholder
        }