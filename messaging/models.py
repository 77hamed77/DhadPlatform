from django.db import models
from core.models import User # لاستيراد نموذج المستخدم المخصص

# 1. نموذج المحادثة
# هذا النموذج يمثل محادثة بين مستخدمين أو مجموعة من المستخدمين.
# يمكن أن يكون بين طالب ومعلم، أو طالب وزميل.
class Conversation(models.Model):
    # المستخدمون المشاركون في هذه المحادثة
    # min_objects=2 لضمان وجود طرفين على الأقل في المحادثة
    participants = models.ManyToManyField(User, related_name='conversations', verbose_name="المشاركون")

    # حقل لتحديد نوع المحادثة (فردية، جماعية)
    CONVERSATION_TYPE_CHOICES = [
        ('private', 'خاصة'), # محادثة بين شخصين
        ('group', 'مجموعة'), # محادثة جماعية (يمكن تطويرها لاحقاً)
    ]
    conversation_type = models.CharField(max_length=10, choices=CONVERSATION_TYPE_CHOICES, default='private', verbose_name="نوع المحادثة")

    # تاريخ إنشاء المحادثة
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    # تاريخ آخر رسالة (لتسهيل ترتيب المحادثات حسب الأحدث)
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ آخر تحديث")

    class Meta:
        verbose_name = "محادثة"
        verbose_name_plural = "المحادثات"
        ordering = ['-updated_at'] # ترتيب المحادثات من الأحدث للأقدم

    def __str__(self):
        # تمثيل بسيط للمحادثة بأسماء المشاركين (مثلاً: "محادثة بين أحمد ومحمد")
        participant_names = ", ".join([user.username for user in self.participants.all()])
        return f"محادثة: {participant_names}"

    # دالة مساعدة للحصول على الطرف الآخر في محادثة فردية
    def get_other_participant(self, current_user):
        if self.conversation_type == 'private' and self.participants.count() == 2:
            for participant in self.participants.all():
                if participant != current_user:
                    return participant
        return None # أو رفع استثناء إذا كانت ليست محادثة فردية

# 2. نموذج الرسالة
# هذا النموذج يمثل رسالة واحدة ضمن محادثة معينة.
class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name="المحادثة")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages', verbose_name="المرسل")
    content = models.TextField(verbose_name="محتوى الرسالة")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="وقت الإرسال")

    # حقل لتتبع إذا كانت الرسالة مقروءة (يمكن تطويره لاحقاً)
    is_read = models.BooleanField(default=False, verbose_name="مقروءة؟")

    class Meta:
        verbose_name = "رسالة"
        verbose_name_plural = "الرسائل"
        ordering = ['timestamp'] # ترتيب الرسائل من الأقدم للأحدث في المحادثة

    def __str__(self):
        return f"رسالة من {self.sender.username} في {self.conversation.id} - {self.timestamp.strftime('%H:%M')}"