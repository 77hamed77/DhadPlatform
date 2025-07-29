# core/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.apps import apps

# --------------------------------------------------------------------------
# نقل DEFINED_LEVEL_CHOICES إلى هنا لتجنب الاستيراد الدائري
# --------------------------------------------------------------------------
# قائمة المستويات المتاحة
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

# تعريف نموذج المستخدم المخصص
class User(AbstractUser):
    USER_ROLES = (
        ('admin', 'مسؤول'),
        ('teacher', 'معلم'),
        ('student', 'طالب'),
    )
    role = models.CharField(max_length=10, choices=USER_ROLES, default='student', verbose_name="الدور")

    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="رقم الواتساب")
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name="الدولة")

    determined_arabic_level = models.CharField(
        max_length=20,
        choices=DETERMINED_LEVEL_CHOICES, # استخدام CHOICES التي تم تعريفها هنا
        default='unassigned',
        blank=True,
        null=True,
        verbose_name="المستوى المحدد (اللغة العربية)",
        help_text="المستوى المحدد للطالب بعد اجتياز اختبار تحديد المستوى."
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        verbose_name="الصورة الشخصية"
    )

    # --------------------------------------------------------------------------
    # إضافة خاصية 'full_name' هنا
    # --------------------------------------------------------------------------
    @property
    def full_name(self):
        """
        يعيد الاسم الكامل للمستخدم، مكونًا من الاسم الأول والاسم الأخير.
        """
        if self.first_name and self.last_name:
            # استخدم strip() لإزالة أي مسافات زائدة
            return f"{self.first_name} {self.last_name}".strip()
        elif self.first_name:
            return self.first_name.strip()
        elif self.last_name:
            return self.last_name.strip()
        return self.username # العودة إلى اسم المستخدم إذا لم يكن هناك اسم أول أو أخير


    class Meta:
        verbose_name = "المستخدم"
        verbose_name_plural = "المستخدمون"

    # تعديل دالة __str__ لاستخدام full_name إن وجد
    def __str__(self):
        return self.full_name or self.username

    # --------------------------------------------------------------------------
    # دوال مساعدة لاسترجاع البرامج والمواد التي ينتمي إليها الطالب
    # يجب استيراد النماذج هنا (عند الحاجة) أو استخدام AppRegistry
    # --------------------------------------------------------------------------
    def get_enrolled_programs(self):
        """
        يرجع قائمة بالبرامج الفريدة التي سجل فيها الطالب.
        """
        if self.role != 'student':
            Program = apps.get_model('academic', 'Program') 
            return Program.objects.none()

        Course = apps.get_model('academic', 'Course')
        Program = apps.get_model('academic', 'Program') 

        enrolled_courses = Course.objects.filter(classes__students=self).distinct()
        programs = Program.objects.filter(courses__in=enrolled_courses).distinct().order_by('name')

        programs_with_courses = []
        for program in programs:
            program_courses = enrolled_courses.filter(program=program).order_by('name')
            programs_with_courses.append({
                'program': program,
                'courses': program_courses
            })
        return programs_with_courses

    def get_enrolled_courses(self):
        """
        يرجع قائمة بالمواد (الكورسات) الفريدة التي سجل فيها الطالب.
        """
        if self.role != 'student':
            Course = apps.get_model('academic', 'Course') 
            return Course.objects.none()
        
        Course = apps.get_model('academic', 'Course') 
        return Course.objects.filter(classes__students=self).distinct().order_by('name')

    # --------------------------------------------------------------------------
    # دالة جديدة: جلب الجلسات القادمة للطالب
    # --------------------------------------------------------------------------
    def get_upcoming_classes(self):
        """
        يرجع قائمة بالحلقات الدراسية (Classes) القادمة التي سجل فيها الطالب.
        """
        if self.role != 'student':
            Class = apps.get_model('academic', 'Class') 
            return Class.objects.none()

        now = timezone.now()
        
        Class = apps.get_model('academic', 'Class') 

        upcoming_classes = Class.objects.filter(
            students=self,
            end_time__gte=now
        ).order_by('start_time')

        return upcoming_classes

    # --------------------------------------------------------------------------
    # **NEW METHOD: get_overall_progress_percentage**
    # This is the method you need to add to your User model.
    # --------------------------------------------------------------------------
    def get_overall_progress_percentage(self):
        """
        Calculates the overall progress percentage for the student.
        This method needs to be implemented based on your academic structure.
        
        Example logic might include:
        1. Percentage of lessons completed within enrolled courses.
        2. Average score on tests taken.
        3. Completion of specific milestones/modules.
        
        For now, this is a placeholder. You must replace it with your actual logic.
        """
        if self.role != 'student':
            return 0  # Only students have progress percentage

        # Dynamically get models from the 'academic' app to avoid circular imports
        Course = apps.get_model('academic', 'Course')
        Lesson = apps.get_model('academic', 'Lesson')
        LessonProgress = apps.get_model('academic', 'LessonProgress') 
        Test = apps.get_model('academic', 'Test')
        TestResult = apps.get_model('academic', 'TestResult') 

        total_progress_points = 0
        achieved_progress_points = 0
        
        # --- Example Progress Logic (You need to customize this heavily) ---
        
        # 1. Progress based on lessons completed
        enrolled_courses = self.get_enrolled_courses() # Reuse the existing method
        total_lessons_in_enrolled_courses = 0
        completed_lessons_count = 0

        for course in enrolled_courses:
            total_lessons_in_course = Lesson.objects.filter(course=course).count()
            total_lessons_in_enrolled_courses += total_lessons_in_course
            
            # Count lessons completed by this student in this course
            completed_lessons_count += LessonProgress.objects.filter(
                student=self,
                lesson__course=course,
                status='completed' # <-- CHANGED THIS LINE: Use status='completed'
            ).count()

        if total_lessons_in_enrolled_courses > 0:
            lesson_completion_percentage = (completed_lessons_count / total_lessons_in_enrolled_courses) * 100
        else:
            lesson_completion_percentage = 0

        # Assign weight to lesson completion (e.g., 70% of overall progress)
        total_progress_points += 70 
        achieved_progress_points += (lesson_completion_percentage / 100) * 70

        # 2. Progress based on test scores (example)
        # Assuming tests are associated with courses or levels
        student_test_results = TestResult.objects.filter(student=self)
        
        total_test_score_sum = 0
        max_possible_test_score_sum = 0
        
        for result in student_test_results:
            total_test_score_sum += result.score
            # Assuming your Test model has a 'max_score' field
            if hasattr(result.test, 'max_score'):
                max_possible_test_score_sum += result.test.max_score
            else:
                # Fallback if Test model doesn't have max_score,
                # or define a default max score per test/question type
                max_possible_test_score_sum += 100 # Example default
        
        if max_possible_test_score_sum > 0:
            test_score_percentage = (total_test_score_sum / max_possible_test_score_sum) * 100
        else:
            test_score_percentage = 0

        # Assign weight to test scores (e.g., 30% of overall progress)
        total_progress_points += 30
        achieved_progress_points += (test_score_percentage / 100) * 30

        # Calculate overall percentage
        if total_progress_points > 0:
            overall_percentage = (achieved_progress_points / total_progress_points) * 100
        else:
            overall_percentage = 0

        return round(overall_percentage, 2)
        
        # --- END Example Progress Logic ---

        # If you don't have detailed academic models yet, you can start with a simple placeholder:
        # return 0 # Or a fixed value for testing, e.g., 50