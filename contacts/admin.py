# C:\projectsDejango\DhadPlatform\contacts\admin.py

from django.contrib import admin
from .models import Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    # Add 'whatsapp_number' to list_display
    list_display = ('name', 'email', 'whatsapp_number', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    # Add 'whatsapp_number' to search_fields
    search_fields = ('name', 'email', 'whatsapp_number', 'subject', 'message')
    # Add 'whatsapp_number' to readonly_fields
    readonly_fields = ('name', 'email', 'whatsapp_number', 'subject', 'message', 'created_at')
    list_editable = ('is_read',)

    fieldsets = (
        (None, {
            'fields': ('name', 'email', 'whatsapp_number', 'subject', 'message') # Add to fieldsets
        }),
        ('معلومات إضافية', {
            'fields': ('created_at', 'is_read')
        }),
    )