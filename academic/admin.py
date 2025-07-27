from django.contrib import admin
from django.utils.html import format_html # لاستخدام HTML في list_display
from django.urls import reverse
from .models import (
    Program, Course, Class, Lesson, EducationalFile,
    Assignment, Submission,
    Test, Question, Option, TestResult
)

# 1. تكوين عرض نموذج Program في لوحة الإدارة
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    list_filter = ('name',)

# 2. تكوين عرض نموذج Course في لوحة الإدارة
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'description')
    search_fields = ('name', 'program__name')
    list_filter = ('program',)
    autocomplete_fields = ['program'] # لتحسين البحث عن البرنامج

# 3. تكوين عرض نموذج Class (الحلقة الدراسية) في لوحة الإدارة
class ClassAdmin(admin.ModelAdmin):
    list_display = ('course', 'teacher', 'start_time', 'end_time', 'capacity', 'current_students_count', 'available_slots', 'is_full', 'required_arabic_level')
    search_fields = ('course__name', 'teacher__username', 'class_code')
    list_filter = ('course', 'teacher', 'required_arabic_level', 'start_time')
    date_hierarchy = 'start_time' # للتنقل الزمني حسب تاريخ البدء
    filter_horizontal = ('students',) # لجعل اختيار الطلاب أسهل في شاشة الإضافة/التعديل
    autocomplete_fields = ['course', 'teacher'] # لتحسين البحث عن المادة والمعلم

    def current_students_count(self, obj):
        return obj.students.count()
    current_students_count.short_description = 'عدد الطلاب الحاليين'

    def available_slots(self, obj):
        return obj.available_slots()
    available_slots.short_description = 'المقاعد المتاحة'

    def is_full(self, obj):
        return obj.is_full()
    is_full.boolean = True
    is_full.short_description = 'ممتلئة؟'

    fieldsets = (
        (None, {
            'fields': ('course', 'teacher', 'class_code', 'capacity', 'required_arabic_level')
        }),
        ('مواعيد الجلسة', {
            'fields': ('start_time', 'end_time')
        }),
        ('الطلاب المسجلون', {
            'fields': ('students',)
        }),
    )

# 4. تكوين عرض نموذج Lesson (الدروس المسجلة) في لوحة الإدارة
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'is_recorded', 'published_date', 'get_youtube_link_display')
    search_fields = ('title', 'course__name')
    list_filter = ('course', 'is_recorded', 'published_date')
    autocomplete_fields = ['course'] # لتحسين البحث عن المادة
    readonly_fields = ('published_date',) # تاريخ النشر يتم إضافته تلقائياً

    def get_youtube_link_display(self, obj):
        if obj.youtube_link:
            return format_html('<a href="{}" target="_blank">رابط الفيديو</a>', obj.youtube_link)
        return "-"
    get_youtube_link_display.short_description = 'رابط يوتيوب'

# 5. تكوين عرض نموذج EducationalFile (الملفات التعليمية) في لوحة الإدارة
class EducationalFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'uploaded_by', 'uploaded_at', 'get_file_link_display')
    search_fields = ('title', 'course__name', 'uploaded_by__username')
    list_filter = ('course', 'uploaded_by', 'uploaded_at')
    autocomplete_fields = ['course', 'uploaded_by'] # لتحسين البحث عن المادة والمستخدم الرافع
    readonly_fields = ('uploaded_at',) # تاريخ الرفع يتم إضافته تلقائياً

    def get_file_link_display(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">عرض/تنزيل الملف</a>', obj.file.url)
        return "لا يوجد ملف"
    get_file_link_display.short_description = 'الملف'

# 6. تكوين عرض نموذج Assignment في لوحة الإدارة
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'due_date', 'max_score', 'created_at', 'view_submissions_link')
    search_fields = ('title', 'description', 'course__name')
    list_filter = ('course', 'due_date')
    date_hierarchy = 'created_at' # للتنقل الزمني
    readonly_fields = ('created_at',)
    autocomplete_fields = ['course'] # لتحسين البحث عن المادة

    def view_submissions_link(self, obj):
        url = reverse('admin:academic_submission_changelist') + f'?assignment__id__exact={obj.id}'
        count = obj.submissions.count()
        return format_html('<a href="{}">عرض التسليمات ({})</a>', url, count)
    view_submissions_link.short_description = 'التسليمات'

# 7. تكوين عرض نموذج Submission في لوحة الإدارة
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'status', 'score', 'teacher_notes', 'view_file_link') # تم إضافة 'teacher_notes' هنا
    search_fields = ('assignment__title', 'student__username', 'student__full_name')
    list_filter = ('status', 'assignment__course', 'submitted_at')
    date_hierarchy = 'submitted_at'
    readonly_fields = ('submitted_at', 'view_file_link')
    list_editable = ('status', 'score', 'teacher_notes') # للسماح بتعديل الحالة والدرجة والملاحظات مباشرة
    autocomplete_fields = ['assignment', 'student'] # لتحسين البحث عن الواجب والطالب

    def view_file_link(self, obj):
        if obj.submitted_file:
            return format_html('<a href="{}" target="_blank">عرض الملف</a>', obj.submitted_file.url)
        return "لا يوجد ملف"
    view_file_link.short_description = 'ملف التسليم'

# 8. Inline للخيارات داخل السؤال (لتظهر في صفحة تفاصيل السؤال أو الاختبار)
class OptionInline(admin.TabularInline):
    model = Option
    extra = 4 # عدد الخيارات الفارغة التي تظهر افتراضياً
    min_num = 2 # على الأقل خيارين
    fields = ('text', 'is_correct')

# 9. Inline للأسئلة داخل الاختبار (لتظهر في صفحة تفاصيل الاختبار)
class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1 # عدد الأسئلة الفارغة التي تظهر افتراضياً
    inlines = [OptionInline] # لعرض الخيارات مباشرة تحت السؤال
    fields = ('text', 'question_type', 'score_points', 'stage') # أضف 'stage' هنا

# 10. تكوين عرض نموذج Test في لوحة الإدارة
class TestAdmin(admin.ModelAdmin):
    # تم إزالة 'due_date', 'max_score'
    list_display = ('title', 'course', 'is_placement_test', 'created_at', 'view_results_link')
    search_fields = ('title', 'description', 'course__name')
    # تم إزالة 'due_date'
    list_filter = ('course', 'is_placement_test')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    inlines = [QuestionInline] # إضافة الأسئلة كـ inline في صفحة تفاصيل الاختبار
    autocomplete_fields = ['course'] # لتحسين البحث عن المادة

    def view_results_link(self, obj):
        url = reverse('admin:academic_testresult_changelist') + f'?test__id__exact={obj.id}'
        count = obj.results.count()
        return format_html('<a href="{}">عرض النتائج ({})</a>', url, count)
    view_results_link.short_description = 'النتائج'

# 11. تكوين عرض نموذج Question في لوحة الإدارة (إذا أردت إدارتها بشكل منفصل)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'test', 'question_type', 'score_points', 'stage') # أضف 'stage' هنا
    search_fields = ('text', 'test__title')
    list_filter = ('test', 'question_type', 'stage') # أضف 'stage' هنا
    inlines = [OptionInline] # لعرض الخيارات مباشرة تحت السؤال
    autocomplete_fields = ['test'] # لتحسين البحث عن الاختبار

# 12. تكوين عرض نموذج Option في لوحة الإدارة (إذا أردت إدارتها بشكل منفصل)
class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    search_fields = ('text', 'question__text')
    list_filter = ('question', 'is_correct')
    autocomplete_fields = ['question'] # لتحسين البحث عن السؤال

# 13. تكوين عرض نموذج TestResult في لوحة الإدارة
class TestResultAdmin(admin.ModelAdmin):
    # تم استبدال 'submitted_at' بـ 'end_time'
    list_display = ('test', 'student', 'score', 'status', 'end_time')
    search_fields = ('test__title', 'student__username', 'student__full_name')
    # تم استبدال 'submitted_at' بـ 'end_time'
    list_filter = ('status', 'test__course', 'end_time')
    # تم استبدال 'submitted_at' بـ 'end_time'
    date_hierarchy = 'end_time'
    # تم استبدال 'submitted_at' بـ 'end_time' وإزالة 'answers'
    readonly_fields = ('end_time',) # 'answers' لا يوجد في النموذج
    list_editable = ('status', 'score',) # للسماح بتعديل الحالة والدرجة مباشرة
    autocomplete_fields = ['test', 'student'] # لتحسين البحث عن الاختبار والطالب


# -----------------------------------------------------------------------------
# تسجيل جميع النماذج في لوحة الإدارة باستخدام فئات Admin المخصصة
# -----------------------------------------------------------------------------
admin.site.register(Program, ProgramAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(EducationalFile, EducationalFileAdmin)
admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Test, TestAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(TestResult, TestResultAdmin)