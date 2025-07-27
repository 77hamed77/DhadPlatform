from django.db import models

class Message(models.Model):
    name = models.CharField(max_length=100, verbose_name="الاسم الكامل")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    subject = models.CharField(max_length=200, verbose_name="الموضوع")
    message = models.TextField(verbose_name="الرسالة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإرسال")
    is_read = models.BooleanField(default=False, verbose_name="تم القراءة")

    class Meta:
        verbose_name = "رسالة اتصال"
        verbose_name_plural = "رسائل الاتصال"
        ordering = ['-created_at'] # ترتيب الرسائل من الأحدث للأقدم

    def __str__(self):
        return f"رسالة من {self.name} - الموضوع: {self.subject[:50]}..."