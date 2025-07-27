from django.contrib import admin
from .models import Conversation, Message

# هذا يسمح لنا بعرض الرسائل المرتبطة بمحادثة معينة مباشرة
# ضمن صفحة تفاصيل تلك المحادثة في لوحة الإدارة
class MessageInline(admin.TabularInline):
    model = Message
    extra = 0  # عدد الرسائل الفارغة التي تظهر بشكل افتراضي
    readonly_fields = ('timestamp', 'sender', 'content') # لجعل الرسائل للقراءة فقط
    can_delete = False # منع حذف الرسائل مباشرة من المحادثة (يمكن تفعيلها إذا أردت)
    # لتحديد الحقول التي تظهر في Inline
    fields = ('sender', 'content', 'timestamp', 'is_read')

# تكوين عرض نموذج Conversation في لوحة الإدارة
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'display_participants', 'conversation_type', 'created_at', 'updated_at')
    search_fields = ('participants__username', 'participants__email')
    list_filter = ('conversation_type', 'created_at', 'updated_at')
    filter_horizontal = ('participants',) # لتحسين واجهة اختيار المشاركين (Many-to-Many)
    readonly_fields = ('created_at', 'updated_at')
    
    # إضافة الرسائل كـ inline في صفحة تفاصيل المحادثة
    inlines = [MessageInline]

    # دالة مساعدة لعرض أسماء المشاركين في قائمة العرض
    def display_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    display_participants.short_description = 'المشاركون'

# تكوين عرض نموذج Message في لوحة الإدارة (إذا أردت إدارتها بشكل منفصل)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'content', 'timestamp', 'is_read')
    search_fields = ('content', 'sender__username', 'conversation__id')
    list_filter = ('timestamp', 'is_read', 'conversation__conversation_type')
    readonly_fields = ('timestamp',) # وقت الإرسال يتم إضافته تلقائياً

# تسجيل النماذج في لوحة الإدارة
admin.site.register(Conversation, ConversationAdmin)
admin.site.register(Message, MessageAdmin)