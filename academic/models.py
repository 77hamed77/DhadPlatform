# academic/models.py

from django.db import models
from django.utils import timezone # لاستخدام timezone في حالة الجلسات

# 1. نموذج البرنامج التعليمي (مثال: برنامج اللغة العربية، برنامج الرياضيات)
class Program(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="اسم البرنامج")
    description = models.TextField(blank=True, null=True, verbose_name="وصف البرنامج")

    class Meta:
        verbose_name = "برنامج تعليمي"
        verbose_name_plural = "برامج تعليمية"
        ordering = ['name'] # ترتيب أبجدي حسب الاسم

    def __str__(self):
        return self.name

# 2. نموذج المادة الدراسية (مثال: مادة القواعد، مادة النحو)
class Course(models.Model):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='courses', verbose_name="البرنامج التابع له")
    name = models.CharField(max_length=255, verbose_name="اسم المادة")
    description = models.TextField(blank=True, null=True, verbose_name="وصف المادة")

    class Meta:
        verbose_name = "مادة دراسية"
        verbose_name_plural = "مواد دراسية"
        unique_together = ('program', 'name') # التأكد أن اسم المادة فريد ضمن البرنامج
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.program.name})"

# 3. نموذج الحلقة الدراسية (التي تجمع الطلاب والمعلم في وقت محدد)
class Class(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='classes', verbose_name="المادة التابعة لها")
    # تم تغيير User إلى 'core.User' لحل مشكلة الاستيراد الدائري
    teacher = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'teacher'}, related_name='taught_classes', verbose_name="المعلم")
    
    class_code = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="رمز الحلقة")

    start_time = models.DateTimeField(verbose_name="وقت بدء الجلسة")
    end_time = models.DateTimeField(verbose_name="وقت انتهاء الجلسة")
    
    # تم تغيير User إلى 'core.User' لحل مشكلة الاستيراد الدائري
    students = models.ManyToManyField('core.User', related_name='enrolled_classes', limit_choices_to={'role': 'student'}, blank=True, verbose_name="الطلاب المسجلون")

    capacity = models.PositiveIntegerField(default=10, verbose_name="سعة الحلقة")

    REQUIRED_LEVEL_CHOICES = [
        ('beginner', 'مبتدئ'),
        ('intermediate', 'متوسط'),
        ('advanced', 'متقدم'),
        ('any', 'أي مستوى'), # لإعطاء مرونة إذا لم يكن المستوى محدداً
    ]
    required_arabic_level = models.CharField(
        max_length=20,
        choices=REQUIRED_LEVEL_CHOICES,
        default='any',
        verbose_name="المستوى العربي المطلوب",
        help_text="المستوى المحدد في اللغة العربية المطلوب للطلاب في هذه الحلقة."
    )

    class Meta:
        verbose_name = "حلقة دراسية"
        verbose_name_plural = "حلقات دراسية"
        ordering = ['start_time']

    def __str__(self):
        teacher_name = self.teacher.get_full_name() if self.teacher else "غير محدد"
        return f"حلقة {self.course.name} - المعلم: {teacher_name} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def current_students_count(self):
        return self.students.count()
    
    def available_slots(self):
        return self.capacity - self.current_students_count()
    
    def is_full(self):
        return self.current_students_count() >= self.capacity

# 4. نموذج الدرس المسجل (فيديو مرتبط بيوتيوب)
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons', verbose_name="المادة التابعة لها")
    title = models.CharField(max_length=255, verbose_name="عنوان الدرس")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الدرس")
    
    youtube_link = models.URLField(verbose_name="رابط فيديو يوتيوب", help_text="الرابط الكامل لفيديو يوتيوب (غير مدرج أو خاص).")
    
    is_recorded = models.BooleanField(default=True, verbose_name="درس مسجل")
    
    published_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ النشر")

    class Meta:
        verbose_name = "درس مسجل"
        verbose_name_plural = "الدروس المسجلة"
        ordering = ['published_date']
        unique_together = ('course', 'title') # التأكد أن عنوان الدرس فريد ضمن المادة

    def __str__(self):
        return f"{self.title} ({self.course.name})"

# 5. نموذج الملف التعليمي (ملفات PDF، مستندات، إلخ)
class EducationalFile(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='educational_files', verbose_name="المادة التابعة لها")
    title = models.CharField(max_length=255, verbose_name="عنوان الملف")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الملف")
    
    file = models.FileField(upload_to='educational_files/', verbose_name="الملف")
    
    # تم تغيير User إلى 'core.User' لحل مشكلة الاستيراد الدائري
    uploaded_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, verbose_name="تم الرفع بواسطة", limit_choices_to={'role__in': ['admin', 'teacher']})
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    class Meta:
        verbose_name = "ملف تعليمي"
        verbose_name_plural = "الملفات التعليمية"
        ordering = ['-uploaded_at']
        unique_together = ('course', 'title') # التأكد أن عنوان الملف فريد ضمن المادة

    def __str__(self):
        return f"{self.title} ({self.course.name})"
    
# 6. نموذج الواجب المطلوب من المعلم
class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments', verbose_name="المادة التابعة لها")
    title = models.CharField(max_length=255, verbose_name="عنوان الواجب")
    description = models.TextField(blank=True, null=True, verbose_name="وصف الواجب")
    due_date = models.DateTimeField(verbose_name="تاريخ التسليم النهائي")
    max_score = models.PositiveIntegerField(default=100, verbose_name="أقصى درجة")
    
    assignment_file = models.FileField(upload_to='assignments_files/', blank=True, null=True, verbose_name="ملف الواجب (اختياري)")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")

    class Meta:
        verbose_name = "واجب"
        verbose_name_plural = "الواجبات"
        ordering = ['due_date']
        unique_together = ('course', 'title') # التأكد أن عنوان الواجب فريد ضمن المادة

    def __str__(self):
        return f"{self.title} ({self.course.name})"

# 7. نموذج تسليم الواجب من قبل الطالب
class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions', verbose_name="الواجب")
    # تم تغيير User إلى 'core.User' لحل مشكلة الاستيراد الدائري
    student = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='submitted_assignments', verbose_name="الطالب")
    
    submitted_file = models.FileField(upload_to='student_submissions/', verbose_name="ملف التسليم")
    
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ التسليم")
    
    STATUS_CHOICES = [
        ('pending', 'قيد المراجعة'),
        ('graded', 'تم التصحيح'),
        ('resubmit', 'مطلوب إعادة تسليم'), # إذا كان هناك حاجة للتعديل
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="الحالة")
    
    score = models.PositiveIntegerField(blank=True, null=True, verbose_name="الدرجة")
    teacher_notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات المعلم")

    class Meta:
        verbose_name = "تسليم واجب"
        verbose_name_plural = "تسليمات الواجبات"
        unique_together = ('assignment', 'student') # الطالب يسلم واجب واحد فقط لكل مهمة
        ordering = ['-submitted_at'] # الأحدث أولاً

    def __str__(self):
        return f"تسليم {self.assignment.title} بواسطة {self.student.username}"
    
# قائمة المستويات المتاحة (تم نقلها للأعلى لتكون متاحة لنموذج Test)
DETERMINED_LEVEL_CHOICES = [
    ('unassigned', 'لم يتم التحديد بعد'), # حالة أولية
    ('A1', 'مستوى A1'),
    ('A2', 'مستوى A2'),
    ('B1', 'مستوى B1'),
    ('B2', 'مستوى B2'),
    ('C1', 'مستوى C1'),
    ('C2', 'مستوى C2'),
    ('native', 'متحدث أصلي'), # لمن يجتاز جميع المستويات العليا
]

# 8. نموذج الاختبار (الاختبارات الدورية أو اختبار تحديد المستوى)
# تم الاحتفاظ بهذا التعريف فقط وإزالة التعريف المكرر في الأعلى
class Test(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان الاختبار")
    description = models.TextField(blank=True, verbose_name="الوصف")
    duration_minutes = models.PositiveIntegerField(default=60, verbose_name="مدة الاختبار بالدقائق")
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True, related_name='tests', verbose_name="المادة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    is_placement_test = models.BooleanField(default=False, verbose_name="هل هو اختبار تحديد مستوى؟")
    level = models.CharField(max_length=20, choices=DETERMINED_LEVEL_CHOICES, blank=True, null=True, verbose_name="المستوى المستهدف")
    next_test_on_success = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_success_tests', verbose_name="الاختبار التالي (نجاح)")
    next_test_on_failure = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_failure_tests', verbose_name="الاختبار السابق (فشل)")

    class Meta:
        verbose_name = "اختبار"
        verbose_name_plural = "اختبارات"
        ordering = ['title']

    def __str__(self):
        return self.title

# 9. نموذج السؤال داخل الاختبار
class Question(models.Model):
    # لا داعي لتغيير Test هنا لأن Test معرف في نفس الملف (بعد التعديل)
    test = models.ForeignKey('Test', on_delete=models.CASCADE, related_name='questions', verbose_name="الاختبار التابع له")
    text = models.TextField(verbose_name="نص السؤال")
    
    QUESTION_TYPE_CHOICES = [
        ('multiple_choice', 'اختيار من متعدد'),
        ('true_false', 'صواب/خطأ'),
        ('short_answer', 'إجابة قصيرة'), # يمكن تطويره لتقييم يدوي
    ]
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES, default='multiple_choice', verbose_name="نوع السؤال")
    
    score_points = models.PositiveIntegerField(default=1, verbose_name="نقاط السؤال")

    STAGE_CHOICES = [
        ('beginner', 'مبتدئ'),
        ('intermediate', 'متوسط'),
        ('advanced', 'متقدم'),
    ]
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default='intermediate', verbose_name="المرحلة", help_text="مرحلة السؤال في اختبار تحديد المستوى")

    class Meta:
        verbose_name = "سؤال"
        verbose_name_plural = "الأسئلة"
        ordering = ['id'] # الترتيب داخل الاختبار

    def __str__(self):
        return f"سؤال ({self.test.title}): {self.text[:50]}..."

# 10. نموذج الخيار لسؤال الاختيار من متعدد
class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='options', verbose_name="السؤال التابع له")
    text = models.CharField(max_length=255, verbose_name="نص الخيار")
    is_correct = models.BooleanField(default=False, verbose_name="إجابة صحيحة؟")

    class Meta:
        verbose_name = "خيار"
        verbose_name_plural = "الخيارات"
        unique_together = ('question', 'text') # الخيار يجب أن يكون فريداً ضمن السؤال

    def __str__(self):
        return f"خيار لـ {self.question.text[:30]}...: {self.text}"

# 11. نموذج لتتبع تقدم الطالب في الدروس
class LessonProgress(models.Model):
    # تم تغيير User إلى 'core.User' لحل مشكلة الاستيراد الدائري
    student = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='lesson_progresses', verbose_name="الطالب")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progresses', verbose_name="الدرس")

    STATUS_CHOICES = [
        ('started', 'بدأ المشاهدة'),
        ('completed', 'شوهد بالكامل'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='started', verbose_name="الحالة")

    last_updated = models.DateTimeField(auto_now=True, verbose_name="آخر تحديث")

    class Meta:
        verbose_name = "تقدم الدرس"
        verbose_name_plural = "تقدم الدروس"
        unique_together = ('student', 'lesson') # الطالب يسجل تقدم لدرس واحد فقط
        ordering = ['-last_updated']

    def __str__(self):
        return f"تقدم {self.student.username} في {self.lesson.title}: {self.get_status_display()}"
    
# 12. نموذج نتيجة الاختبار (تعديل TestResult)
# (تم تغيير الرقم التسلسلي ليتوافق مع الترتيب الجديد بعد إزالة التعريف المكرر لـ Test)
class TestResult(models.Model):
    # تم تغيير User إلى 'core.User' لحل مشكلة الاستيراد الدائري
    student = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='test_results', verbose_name="الطالب")
    # لا داعي لتغيير Test هنا لأن Test معرف في نفس الملف
    test = models.ForeignKey('Test', on_delete=models.CASCADE, related_name='results', verbose_name="الاختبار")
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="وقت البدء")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="وقت الانتهاء")
    score = models.IntegerField(null=True, blank=True, verbose_name="النتيجة")
    passed = models.BooleanField(null=True, blank=True, verbose_name="اجتاز") # هل اجتاز الاختبار ككل

    determined_level_at_this_stage = models.CharField(
        max_length=20,
        choices=DETERMINED_LEVEL_CHOICES,
        default='unassigned',
        verbose_name="المستوى المحدد من هذه المرحلة"
    )

    is_final_placement_result = models.BooleanField(default=False, verbose_name="هل هي نتيجة تحديد المستوى النهائية؟")

    STATUS_CHOICES = [
        ('in_progress', 'قيد التقدم'),
        ('completed', 'اكتملت هذه المرحلة'),
        ('finalized', 'تم تحديد المستوى النهائي'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress', verbose_name="حالة الاختبار")

    class Meta:
        verbose_name = "نتيجة اختبار"
        verbose_name_plural = "نتائج الاختبارات"
        unique_together = ('test', 'student') # الطالب يمكنه تقديم اختبار واحد فقط (أو نسخة واحدة)
        ordering = ['-start_time']

    def __str__(self):
        return f"نتيجة {self.student.username} لـ {self.test.title}"
    
