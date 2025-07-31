# C:\projectsDejango\DhadPlatform\contacts\models.py

from django.db import models
from django.utils import timezone

class Message(models.Model):
    name = models.CharField(max_length=100, verbose_name="الاسم الكامل")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    
    # حقل رقم الواتساب المدمج
    whatsapp_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="رقم الواتساب (اختياري)",
        help_text="يتم تجميعه تلقائياً من رمز الدولة والرقم المحلي"
    )
    
    subject = models.CharField(max_length=200, verbose_name="الموضوع")
    message = models.TextField(verbose_name="الرسالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    is_read = models.BooleanField(default=False, verbose_name="تم القراءة")

    class Meta:
        verbose_name = "رسالة اتصال"
        verbose_name_plural = "رسائل الاتصال"
        ordering = ['-created_at']

    def __str__(self):
        # تم تصحيح الخطأ هنا: subject بحرف صغير
        return f"رسالة من {self.name} - الموضوع: {self.subject[:50]}..."