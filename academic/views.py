# academic/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q # For OR operations in queries
import json # For storing JSON data in TestResult answers (if still desired, otherwise StudentAnswer is primary)
from django.conf import settings # For accessing settings.py values (e.g., ARABIC_PLACEMENT_COURSE_ID)
from django.utils import timezone # For timezone-aware datetime operations
from django.http import JsonResponse, HttpResponse # استيراد JsonResponse و HttpResponse

# Import all models from academic app, including the new StudentAnswer
from .models import (
    Course,
    Lesson,
    EducationalFile,
    Class,
    Assignment,
    Submission,
    Test,
    Question,
    Option,
    TestResult,
    LessonProgress,
    StudentAnswer, # NEWLY ADDED IMPORT
    DETERMINED_LEVEL_CHOICES # استيراد المستويات
)

# Importing forms from the current app
from .forms import SubmissionForm, BaseTestForm

# Importing User model from core app
from core.models import User # Ensure this is correct based on your project structure

@login_required
def course_detail(request, course_id):
    """
    Displays the details of a specific course, including lessons, educational files,
    assignments, and classmates. Checks for student subscription status.
    """
    course = get_object_or_404(Course, id=course_id)

    is_subscribed = False
    classmates = [] # List of classmates in the same class for this course
    student_class = None # Initialize student_class here

    # Check if the user is a student and is subscribed to this course
    if request.user.role == 'student':
        # Get the specific class instance the student is enrolled in for this course
        student_class = Class.objects.filter(course=course, students=request.user).first()
        if student_class:
            is_subscribed = True
            # Get all students in this class, excluding the current user
            classmates = student_class.students.exclude(id=request.user.id).order_by('first_name', 'last_name')

    # Fetch lessons and educational files for the course
    lessons = Lesson.objects.filter(course=course).order_by('published_date')
    educational_files = EducationalFile.objects.filter(course=course).order_by('-uploaded_at')

    # Logic for assignments
    assignments_data = []
    if is_subscribed: # Assignments are only visible to subscribed students
        assignments_qs = Assignment.objects.filter(course=course).order_by('due_date')
        for assignment in assignments_qs:
            # Check if the student has already submitted this assignment
            submitted = Submission.objects.filter(assignment=assignment, student=request.user).first()

            assignments_data.append({
                'assignment': assignment,
                'submitted_data': submitted, # Submission data if already submitted
                'has_submitted': submitted is not None,
                'submission_form': SubmissionForm() # An empty form for each assignment
            })

    context = {
        'course': course,
        'is_subscribed': is_subscribed,
        'student_class': student_class, # Pass the student_class object
        'lessons': lessons,
        'educational_files': educational_files,
        'youtube_embed_base_url': 'https://www.youtube.com/embed/', # Correct YouTube embed base URL
        'assignments': assignments_data, # Pass assignment data
        'classmates': classmates, # Pass classmates list to the template
    }
    return render(request, 'academic/course_detail.html', context)

@login_required
def submit_assignment(request, assignment_id):
    """
    Handles the submission of an assignment by a student.
    """
    # Ensure the request method is POST
    if request.method != 'POST':
        messages.error(request, 'Request method not allowed.')
        return redirect('dashboard')

    assignment = get_object_or_404(Assignment, id=assignment_id)

    # Ensure the user is a student
    if request.user.role != 'student':
        messages.error(request, 'You do not have permission to submit assignments.')
        return redirect('dashboard')

    # Check if the student is subscribed to the course associated with the assignment
    is_subscribed = False
    if Class.objects.filter(course=assignment.course, students=request.user).exists():
        is_subscribed = True

    if not is_subscribed:
        messages.error(request, 'You must be subscribed to the course to submit this assignment.')
        return redirect('academic:course_detail', course_id=assignment.course.id) # Use namespace

    # Check if the student has already submitted this assignment
    existing_submission = Submission.objects.filter(assignment=assignment, student=request.user).first()
    if existing_submission:
        messages.info(request, 'You have already submitted this assignment. You can update the submission file if allowed.')
        # If allowing updates, you would modify the existing_submission here
        return redirect('academic:course_detail', course_id=assignment.course.id) # Use namespace

    form = SubmissionForm(request.POST, request.FILES) # Important: pass request.FILES for file uploads
    if form.is_valid():
        submission = form.save(commit=False) # Do not save immediately
        submission.assignment = assignment
        submission.student = request.user
        submission.status = 'pending' # Set default status
        submission.save()

        messages.success(request, f'Assignment "{assignment.title}" submitted successfully! It will be reviewed.')
        return redirect('academic:course_detail', course_id=assignment.course.id) # Use namespace
    else:
        messages.error(request, 'Assignment submission failed. Please ensure a file is selected.')
        # Redirect back to the course detail page to display errors
        return redirect('academic:course_detail', course_id=assignment.course.id) # Use namespace


@login_required
def test_list(request):
    """
    يعرض قائمة الاختبارات المتاحة للطالب.
    بالنسبة لاختبارات تحديد المستوى، يتم عرض نقطة البداية (A1) إذا لم يحدد مستوى الطالب بعد.
    """
    if request.user.role != 'student':
        # للمدرسين والمسؤولين، اعرض جميع الاختبارات
        tests = Test.objects.all().order_by('title')
        context = {'tests': [{'test': test, 'status': 'N/A', 'result': None} for test in tests]}
        return render(request, 'academic/test_list.html', context)

    # منطق خاص بالطلاب
    tests_for_display = []

    # أولاً، تحقق مما إذا كان الطالب لديه مستوى محدد بالفعل
    if request.user.determined_arabic_level != 'unassigned':
        messages.info(request, f"لقد تم تحديد مستواك في اللغة العربية مسبقاً: {request.user.get_determined_arabic_level_display()}.")
        # لا نعرض اختبارات تحديد المستوى إذا كان المستوى محددًا
        # يمكننا عرض اختبارات الدورات العادية التي التحق بها الطالب هنا
        enrolled_courses_ids = request.user.get_enrolled_courses().values_list('id', flat=True)
        regular_tests = Test.objects.filter(course__id__in=enrolled_courses_ids, is_placement_test=False).order_by('-created_at')
        for test in regular_tests:
            result = TestResult.objects.filter(test=test, student=request.user).first()
            tests_for_display.append({
                'test': test,
                'result': result,
                'status': result.status if result else 'not_started'
            })
    else:
        # إذا لم يتم تحديد مستوى الطالب بعد، ابحث عن اختبار تحديد المستوى الحالي أو A1
        current_placement_test_result = TestResult.objects.filter(
            student=request.user,
            test__is_placement_test=True,
            status='in_progress' # ابحث عن اختبار تحديد مستوى قيد التقدم
        ).order_by('-start_time').first()

        if current_placement_test_result:
            # إذا كان هناك اختبار قيد التقدم، اعرضه للطالب للمتابعة
            tests_for_display.append({
                'test': current_placement_test_result.test,
                'result': current_placement_test_result,
                'status': 'in_progress'
            })
            messages.info(request, f"لديك اختبار تحديد مستوى قيد التقدم: {current_placement_test_result.test.title}. أكمله لتحديد مستواك.")
        else:
            # إذا لم يكن هناك اختبار قيد التقدم ولم يتم تحديد مستوى، اعرض اختبار A1 كنقطة بداية
            initial_placement_test = Test.objects.filter(is_placement_test=True, level='A1').first()
            if initial_placement_test:
                tests_for_display.append({
                    'test': initial_placement_test,
                    'result': None,
                    'status': 'not_started'
                })
            else:
                messages.warning(request, "لا يوجد اختبار تحديد مستوى أساسي (A1) متاح حالياً. يرجى التواصل مع الإدارة.")

        # إضافة أي اختبارات عادية أخرى للطالب (مثلاً من الدورات المسجل فيها)
        enrolled_courses_ids = request.user.get_enrolled_courses().values_list('id', flat=True)
        regular_tests = Test.objects.filter(course__id__in=enrolled_courses_ids, is_placement_test=False).order_by('-created_at')
        for test in regular_tests:
            result = TestResult.objects.filter(test=test, student=request.user).first()
            tests_for_display.append({
                'test': test,
                'result': result,
                'status': result.status if result else 'not_started'
            })


    context = {
        'tests': tests_for_display
    }
    return render(request, 'academic/test_list.html', context)


@login_required
def start_test(request, test_id):
    """
    يبدأ اختبارًا أو يواصل اختبار تحديد مستوى غير مكتمل.
    """
    test = get_object_or_404(Test, id=test_id)
    student_user = request.user

    if student_user.role != 'student':
        messages.error(request, 'أنت لا تملك الصلاحية لبدء الاختبارات.')
        return redirect('academic:test_list')

    # منطق خاص باختبارات تحديد المستوى
    if test.is_placement_test:
        # إذا كان مستوى الطالب محددًا بالفعل، يمنع من بدء اختبار تحديد مستوى جديد.
        if student_user.determined_arabic_level != 'unassigned':
            messages.warning(request, f"لقد تم تحديد مستواك مسبقاً كـ {student_user.get_determined_arabic_level_display()}. لا يمكنك البدء باختبار تحديد مستوى جديد.")
            return redirect('academic:test_list')

        # البحث عن نتيجة اختبار تحديد مستوى جارية لهذا الطالب (لم تُحدد بعد)
        current_placement_test_result = TestResult.objects.filter(
            student=student_user,
            test__is_placement_test=True,
            status='in_progress' # ابحث عن اختبار تحديد مستوى قيد التقدم
        ).order_by('-start_time').first()

        if current_placement_test_result:
            # إذا كان هناك اختبار تحديد مستوى قيد التقدم، وتطابق test_id مع الاختبار الحالي للطالب
            if current_placement_test_result.test.id == test_id:
                messages.info(request, f"تواصل اختبار تحديد المستوى: {test.title}.")
                test_result = current_placement_test_result
            else:
                # إذا كان test_id لا يتطابق، نوجه الطالب إلى الاختبار الجاري
                messages.info(request, f"لديك اختبار تحديد مستوى آخر قيد التقدم: {current_placement_test_result.test.title}. سيتم توجيهك إليه.")
                return redirect('academic:start_test', test_id=current_placement_test_result.test.id)
        else:
            # إذا لم يكن هناك اختبار تحديد مستوى قيد التقدم، ابدأ هذا الاختبار
            messages.info(request, f"بدء اختبار تحديد مستوى جديد: {test.title}.")
            test_result = TestResult.objects.create(
                student=student_user,
                test=test,
                status='in_progress', # تحديد الحالة كـ "قيد التقدم"
                # answers will be populated by StudentAnswer instances
            )

        # الأسئلة لهذا الاختبار المعين
        questions = test.questions.all().order_by('?')
        if not questions.exists():
            messages.error(request, f'لا توجد أسئلة لهذا الاختبار: {test.title}. يرجى التواصل مع الإدارة.')
            return redirect('academic:test_list')

        # Always re-create the form to ensure questions are fresh
        # and test_result_instance is correctly linked for POST submissions.
        form = BaseTestForm(questions=questions, test_result_instance=test_result) # Pass test_result_instance

        context = {
            'test': test,
            'form': form,
            'test_result': test_result, # Pass the test_result object directly
            'questions': questions,
            'is_placement_test': True,
        }
        return render(request, 'academic/start_test.html', context)

    # منطق الاختبارات العادية (ليست تحديد مستوى)
    else:
        # تحقق مما إذا كان الطالب قد أجرى هذا الاختبار العادي من قبل
        existing_result = TestResult.objects.filter(test=test, student=student_user).first()
        if existing_result and existing_result.status in ['completed', 'finalized']:
            messages.info(request, f'لقد أكملت هذا الاختبار مسبقاً. نتيجتك: {existing_result.score}.')
            return redirect('academic:test_result_detail', test_result_id=existing_result.id) # Redirect to result page

        questions = test.questions.all().order_by('?')
        if not questions.exists():
            messages.error(request, 'لا توجد أسئلة لهذا الاختبار.')
            return redirect('academic:test_list')

        # إنشاء نتيجة اختبار جديدة للاختبارات العادية
        test_result = TestResult.objects.create(
            test=test,
            student=student_user,
            status='in_progress',
            score=0,
        )

        form = BaseTestForm(questions=questions, test_result_instance=test_result) # Pass test_result_instance

        context = {
            'test': test,
            'form': form,
            'test_result': test_result, # Pass the test_result object directly
            'questions': questions,
            'is_placement_test': False,
        }
        return render(request, 'academic/start_test.html', context)


@login_required
def submit_test(request, test_result_id):
    """
    يتعامل مع تسليم إجابات الاختبار، ويحسب النتيجة، ويطبق منطق تحديد المستوى متعدد المراحل.
    """
    if request.method != 'POST':
        messages.error(request, 'طريقة الطلب غير مسموح بها.')
        return redirect('dashboard')

    test_result = get_object_or_404(TestResult, id=test_result_id, student=request.user)
    test = test_result.test
    student_user = request.user

    # منع إعادة الإرسال إذا كان الاختبار قد تم إرساله بالفعل أو انتهى
    if test_result.status in ['completed', 'finalized']:
        messages.info(request, 'لقد قمت بإرسال هذا الاختبار مسبقاً.')
        return redirect('academic:test_result_detail', test_result_id=test_result.id) # Redirect to result page

    # Get all questions that were part of this test instance
    questions_for_form = test.questions.all().order_by('id') # Ensure consistent order

    # Pass the test_result_instance to the form for validation and answer saving
    form = BaseTestForm(request.POST, questions=questions_for_form, test_result_instance=test_result)

    if form.is_valid():
        # Call the form's method to save answers and update the TestResult
        form.save_answers_and_update_test_result()

        # After saving, the test_result object will have its score and status updated by the form.
        # We need to re-fetch or use the updated test_result from the form for placement logic.
        # Since the form updates the instance passed to it, `test_result` here is already updated.

        max_score = sum(q.score_points for q in questions_for_form if q.question_type != 'short_answer') # Only auto-gradable questions
        percentage_score = (test_result.score / max_score) * 100 if max_score > 0 else 0

        # ----------------------------------------------------------------------
        # منطق الاختبارات تحديد المستوى متعدد المراحل
        # ----------------------------------------------------------------------
        if test.is_placement_test:
            SUCCESS_THRESHOLD = 80 # للانتقال للمستوى التالي (higher level)
            PASS_THRESHOLD = 50 # لتحديد مستوى الطالب بهذا المستوى

            # test_result.status is already 'completed' from form.save_answers_and_update_test_result()
            # test_result.passed is also set by the form based on `form.score` against thresholds if any logic was there

            if percentage_score >= SUCCESS_THRESHOLD and test.next_test_on_success:
                # أداء ممتاز: ينتقل الطالب لاختبار المستوى التالي (أعلى)
                # test_result.determined_level_at_this_stage and passed are ideally set by the form
                test_result.determined_level_at_this_stage = test.level # Ensure this is set
                test_result.passed = True # Ensure this is set
                test_result.status = 'completed' # Ensure this is set
                test_result.save() # Save any changes made here after form save

                messages.success(request, f"أداء ممتاز في {test.title}! سيتم توجيهك إلى اختبار المستوى التالي ({test.next_test_on_success.title}).")
                return redirect('academic:start_test', test_id=test.next_test_on_success.id)

            elif percentage_score >= PASS_THRESHOLD:
                # أداء متوسط: يتم تحديد مستوى الطالب بهذا المستوى بشكل نهائي
                test_result.determined_level_at_this_stage = test.level
                test_result.is_final_placement_result = True
                test_result.status = 'finalized'
                test_result.passed = True
                student_user.determined_arabic_level = test.level
                student_user.save() # حفظ المستوى المحدد في ملف المستخدم
                test_result.save() # Save any changes made here after form save

                messages.success(request, f"تهانينا! تم تحديد مستواك في اللغة العربية كـ {student_user.get_determined_arabic_level_display()}.")
                # محاولة البحث عن حصة مناسبة للطالب وتفعيله
                found_class_and_activate_student(request, student_user, student_user.determined_arabic_level)
                return redirect('dashboard')

            else: # percentage_score < PASS_THRESHOLD
                # أداء ضعيف: ينتقل الطالب لاختبار المستوى السابق (أدنى) إن وجد
                test_result.determined_level_at_this_stage = test.level # يسجل المستوى الذي فشل فيه
                test_result.passed = False
                test_result.status = 'completed' # Still completed, just not passed
                test_result.save() # Save any changes made here after form save

                if test.next_test_on_failure:
                    messages.warning(request, f"نتيجتك في {test.title} تتطلب منك إعادة اختبار تحديد المستوى بمستوى أدنى. سيتم توجيهك الآن إلى {test.next_test_on_failure.title}.")
                    return redirect('academic:start_test', test_id=test.next_test_on_failure.id)
                else:
                    # إذا لم يكن هناك اختبار أدنى متاح (وصل إلى أدنى مستوى ولم ينجح فيه)
                    # يتم تعيينه للمستوى الأدنى (A1) وتفعيله أو تجميده
                    student_user.determined_arabic_level = 'A1' # Or 'unassigned' if admin intervention is needed
                    student_user.save()
                    test_result.is_final_placement_result = True
                    test_result.status = 'finalized'
                    test_result.save() # Save any changes made here after form save
                    messages.error(request, f"لم تتمكن من اجتياز اختبار {test.title}. تم تحديد مستواك المبدئي كـ {student_user.get_determined_arabic_level_display()}.")
                    # محاولة البحث عن حصة مناسبة للطالب وتفعيله حتى لو كان A1
                    found_class_and_activate_student(request, student_user, student_user.determined_arabic_level)
                    return redirect('dashboard')

        # ----------------------------------------------------------------------
        # منطق الاختبارات العادية (ليست تحديد مستوى)
        # ----------------------------------------------------------------------
        else:
            # For regular tests, the score and status are set by the form's save method.
            # We just need to display the message and redirect.
            pass_threshold = getattr(settings, 'REGULAR_TEST_PASS_THRESHOLD', 60)
            percentage_score_for_regular = (test_result.score / max_score) * 100 if max_score > 0 else 0

            if percentage_score_for_regular >= pass_threshold:
                messages.success(request, f"تهانينا! لقد اجتزت اختبار {test.title} بنجاح. نتيجتك: {test_result.score}/{max_score}")
            else:
                messages.error(request, f"لم تتمكن من اجتياز اختبار {test.title}. نتيجتك: {test_result.score}/{max_score}. يرجى المحاولة مرة أخرى.")

            return redirect('academic:test_result_detail', test_result_id=test_result.id)


    else: # Form is not valid
        messages.error(request, "حدث خطأ أثناء إرسال الاختبار. يرجى مراجعة إجاباتك.")
        questions_to_display = test.questions.all().order_by('id') # Order for consistent display

        context = {
            'test': test,
            'form': form, # The form containing errors
            'test_result': test_result, # The test_result object
            'questions': questions_to_display,
            'is_placement_test': test.is_placement_test,
        }
        return render(request, 'academic/start_test.html', context)


@login_required
def test_result_detail(request, test_result_id):
    """
    Displays the detailed results of a specific test attempt for a student.
    """
    test_result = get_object_or_404(TestResult, id=test_result_id, student=request.user)

    # Retrieve all answers submitted for this test result from the new StudentAnswer model
    student_answers = StudentAnswer.objects.filter(test_result=test_result).select_related('question', 'selected_option').order_by('question__id')

    # Get all questions for the test to calculate total points possible
    all_questions_for_test = test_result.test.questions.all()
    # Calculate max possible score only from auto-gradable questions if short_answer is manually graded
    max_possible_score = sum(q.score_points for q in all_questions_for_test if q.question_type != 'short_answer')

    # Calculate score percentage for display
    score_percentage = 0
    if max_possible_score > 0:
        score_percentage = (test_result.score / max_possible_score) * 100

    # Calculate completion time for display
    completion_time_seconds = None
    if test_result.start_time and test_result.end_time:
        completion_time_seconds = (test_result.end_time - test_result.start_time).total_seconds()


    context = {
        'test_result': test_result,
        'student_answers': student_answers,
        'max_possible_score': max_possible_score,
        'score_percentage': score_percentage,
        'completion_time_seconds': completion_time_seconds,
        'page_title': f"نتائج اختبار: {test_result.test.title}",
    }
    return render(request, 'academic/test_result_detail.html', context)


# دالة مساعدة (Helper function) للبحث عن حصة وتفعيل الطالب
def found_class_and_activate_student(request, student_user, determined_level):
    """
    تبحث عن حصة مناسبة للطالب بناءً على مستواه المحدد وتحاول تسجيله.
    ثم تقوم بتفعيل حساب الطالب بناءً على نتيجة البحث.
    """
    found_class = None
    try:
        arabic_course = None
        # First, try to get the course by ID from settings
        if hasattr(settings, 'ARABIC_PLACEMENT_COURSE_ID') and settings.ARABIC_PLACEMENT_COURSE_ID:
            arabic_course = Course.objects.filter(id=settings.ARABIC_PLACEMENT_COURSE_ID).first()

        # If not found by ID, try to find one marked as 'is_placement_course'
        if not arabic_course:
            arabic_course = Course.objects.filter(is_placement_course=True).first()

        if arabic_course:
            # البحث عن حصص في هذه المادة تطابق المستوى المحدد للطالب أو 'any'
            # Note: The `required_arabic_level` choices in Class model should align with `DETERMINED_LEVEL_CHOICES`
            available_classes = Class.objects.filter(
                course=arabic_course,
                required_arabic_level__in=[determined_level, 'any'], # Check for specific level or 'any'
                start_time__gt=timezone.now(), # حصص مستقبلية فقط
            ).exclude(students=student_user).order_by('start_time')

            for cls in available_classes:
                if not cls.is_full(): # التأكد من وجود أماكن متاحة
                    found_class = cls
                    break
        else:
            messages.warning(request, 'لم يتم تحديد المادة الأساسية لاختبار تحديد المستوى في النظام.')

    except Exception as e:
        messages.error(request, f'حدث خطأ أثناء البحث عن حصص مناسبة: {e}')

    if found_class:
        found_class.students.add(student_user) # تسجيل الطالب في الحصة
        student_user.is_active = True # تفعيل حساب الطالب
        student_user.save()
        messages.success(request, f'تهانينا! لقد تم تسجيلك تلقائياً في حصة "{found_class.course.name}" مع المعلم {found_class.teacher.get_full_name() or found_class.teacher.username}.')
    else:
        # إذا لم يتم العثور على حصة مناسبة
        student_user.is_active = False # تجميد حساب الطالب
        student_user.save()
        messages.warning(request, 'لا توجد حصة مناسبة لمستواك في الوقت الحالي. سيقوم فريق الإدارة بالتواصل معك قريباً لترتيب حصتك.')


@login_required
def mark_lesson_as_completed(request, lesson_id):
    """
    واجهة AJAX لتسجيل الدرس كمشاهد بالكامل.
    """
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        lesson = get_object_or_404(Lesson, id=lesson_id)

        # التأكد أن المستخدم هو طالب
        if request.user.role != 'student':
            return JsonResponse({'status': 'error', 'message': 'You do not have permission.'}, status=403)

        # التحقق مما إذا كان الطالب مشتركاً في المادة المرتبطة بالدرس
        is_subscribed = Class.objects.filter(course=lesson.course, students=request.user).exists()
        if not is_subscribed:
            return JsonResponse({'status': 'error', 'message': 'You must be subscribed to this course to mark lessons as completed.'}, status=403)

        # إنشاء أو تحديث سجل التقدم
        lesson_progress, created = LessonProgress.objects.update_or_create(
            student=request.user,
            lesson=lesson,
            defaults={'status': 'completed'}
        )

        if created:
            message = 'Lesson marked as completed.'
        else:
            message = 'Lesson progress updated to completed.'

        return JsonResponse({'status': 'success', 'message': message})
    return HttpResponse(status=400) # إذا لم يكن طلب AJAX أو طريقة غير صحيحة