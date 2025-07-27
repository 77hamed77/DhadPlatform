from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # استيراد UserAdmin الأصلي
from .models import User # استيراد نموذج المستخدم المخصص الخاص بنا

# لتخصيص عرض نموذج المستخدم في لوحة الإدارة
class CustomUserAdmin(BaseUserAdmin):
    # إضافة الحقول المخصصة إلى قائمة العرض (list_display)
    list_display = BaseUserAdmin.list_display + ('role', 'determined_arabic_level', 'phone_number', 'country')
    
    # إضافة الحقول المخصصة إلى فلاتر القائمة (list_filter)
    list_filter = BaseUserAdmin.list_filter + ('role', 'determined_arabic_level')
    
    # إضافة الحقول المخصصة إلى حقول البحث (search_fields)
    search_fields = BaseUserAdmin.search_fields + ('phone_number', 'country')
    
    # إضافة الحقول المخصصة إلى مجموعات الحقول في صفحة التفاصيل (fieldsets)
    # يجب أن تقوم بتعديل هذا بعناية ليتناسب مع ترتيبك المفضل
    fieldsets = BaseUserAdmin.fieldsets + (
        ('معلومات إضافية', {'fields': ('role', 'determined_arabic_level', 'phone_number', 'country', 'profile_picture')}), # Added profile_picture here too
    )
    
    # إذا كنت تريد جعل حقل determined_arabic_level للقراءة فقط في لوحة الإدارة
    # (لأن النظام سيقوم بتحديده تلقائياً بعد الاختبار)
    # readonly_fields = BaseUserAdmin.readonly_fields + ('determined_arabic_level',) # Uncomment if needed


# إلغاء تسجيل UserAdmin الافتراضي أولاً (إذا كان مسجلاً)
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# تسجيل نموذج المستخدم المخصص الخاص بنا مع فئة Admin المخصصة
admin.site.register(User, CustomUserAdmin)