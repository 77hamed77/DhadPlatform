from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at') # هذه الحقول للقراءة فقط في لوحة الإدارة
    list_editable = ('is_read',) # السماح بتغيير حالة "تم القراءة" مباشرة من القائمة

    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'subject', 'message')
        }),
        ('معلومات إضافية', {
            'fields': ('created_at', 'is_read')
        }),
    )