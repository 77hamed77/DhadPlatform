# registration/models.py
from django.db import models
from core.models import User 

class RegistrationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد الانتظار'),
        ('approved', 'تمت الموافقة'),
        ('rejected', 'تم الرفض'),
    ]

    PAYMENT_METHOD_CHOICES = [ 
        ('shamcash', 'شام كاش'),
        ('bank_transfer', 'حوالات بنكية'),
        ('credit_card', 'بطاقة ائتمان'),
    ]

    full_name = models.CharField(max_length=255, verbose_name="الاسم الكامل")
    date_of_birth = models.DateField(verbose_name="تاريخ الميلاد")
    gender = models.CharField(max_length=10, choices=[('male', 'ذكر'), ('female', 'أنثى')], verbose_name="الجنس")
    country = models.CharField(max_length=100, verbose_name="الدولة")
    current_location = models.CharField(max_length=255, blank=True, null=True, verbose_name="المكان الحالي (المدينة/المنطقة)")
    study_level = models.CharField(max_length=100, verbose_name="المستوى الدراسي")
    curriculum = models.CharField(max_length=100, blank=True, null=True, verbose_name="منهاج الدراسة")
    program = models.CharField(max_length=100, verbose_name="البرنامج الذي يرغب في الانضمام إليه")
    grade = models.CharField(max_length=50, verbose_name="الصف/المستوى الأكاديمي")
    arabic_level = models.CharField(max_length=100, verbose_name="مستوى اللغة العربية الحالي")
    native_language = models.CharField(max_length=100, verbose_name="اللغة الأم")
    email = models.EmailField(unique=True, verbose_name="البريد الإلكتروني")
    whatsapp_number = models.CharField(max_length=20, verbose_name="رقم واتساب للتواصل")

    # تمت إزالة password_hash هنا
    # password_hash = models.CharField(max_length=128, verbose_name="كلمة المرور المشفرة")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="حالة الطلب")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الطلب")
    approved_at = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ الموافقة")
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='registration_request_link', verbose_name="المستخدم المرتبط")

    preferred_payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        blank=True,
        null=True,
        verbose_name="طريقة الدفع المفضلة"
    )

    def __str__(self):
        return f"طلب تسجيل من {self.full_name} ({self.email}) - {self.status}"

    class Meta:
        verbose_name = "طلب تسجيل"
        verbose_name_plural = "طلبات التسجيل"