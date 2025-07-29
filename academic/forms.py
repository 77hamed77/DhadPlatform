# academic/forms.py

from django import forms
from .models import Submission, Question, Option, TestResult, StudentAnswer # استيراد نماذج الاختبارات
from collections import OrderedDict # للحفاظ على ترتيب حقول النموذج
from django.utils import timezone # Add this import for timezone.now()


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        # الطالب يحتاج فقط لرفع الملف. باقي الحقول (assignment, student, status, score, notes) يتم تعيينها برمجياً.
        fields = ['submitted_file']
        labels = {
            'submitted_file': 'ملف تسليم الواجب',
        }
        widgets = {
            'submitted_file': forms.FileInput(attrs={'class': 'block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none'})
        }


class BaseTestForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # 1. Pop custom arguments first
        self.questions = kwargs.pop('questions')
        # FIX: Pop 'test_result_instance' as it's passed from the view
        self.test_result_instance = kwargs.pop('test_result_instance', None)
        self.test_instance_id = kwargs.pop('test_instance_id', None) # Assuming you still want this, though test_result_instance has the test

        # 2. Call the parent constructor with the remaining args/kwargs
        super().__init__(*args, **kwargs)

        # Ensure self.fields is an OrderedDict for consistent ordering
        self.fields = OrderedDict()

        for q in self.questions:
            field_name = f'question_{q.id}'
            if q.question_type == 'multiple_choice':
                choices = [(str(option.id), option.text) for option in q.options.all()]
                self.fields[field_name] = forms.ChoiceField(
                    label=q.text,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-radio'}),
                    required=True
                )
            elif q.question_type == 'true_false':
                choices = [('True', 'صحيح'), ('False', 'خطأ')]
                self.fields[field_name] = forms.ChoiceField(
                    label=q.text,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-radio'}),
                    required=True
                )
            elif q.question_type == 'short_answer':
                self.fields[field_name] = forms.CharField(
                    label=q.text,
                    widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-input'}),
                    required=True
                )
            # يمكنك إضافة أنواع أسئلة أخرى هنا

        # إضافة حقل مخفي لتمرير معرف الاختبار (إذا كنت لا تزال تحتاجه بعد تمرير test_result_instance)
        # Note: test_result_instance already links to the test, so this might be redundant
        # unless you have a specific reason to pass the test_instance_id separately.
        if self.test_instance_id:
            self.fields['test_instance_id'] = forms.CharField(widget=forms.HiddenInput(), initial=self.test_instance_id)


    # دالة للتحقق من الإجابات وحساب الدرجة
    def clean(self):
        cleaned_data = super().clean()
        self.score = 0 # Initialize score
        self.student_answers_data = [] # To store data for StudentAnswer creation

        if not self.test_result_instance:
            # This should ideally not happen if the view handles it correctly
            raise forms.ValidationError("Test result instance is missing.")

        for q in self.questions:
            field_name = f'question_{q.id}'
            answer_value = cleaned_data.get(field_name)

            if answer_value is not None:
                is_correct = False
                selected_option = None
                short_answer_text = None

                if q.question_type == 'multiple_choice':
                    try:
                        selected_option = Option.objects.get(id=int(answer_value))
                        if selected_option.is_correct:
                            is_correct = True
                            self.score += q.score_points
                    except (ValueError, Option.DoesNotExist):
                        is_correct = False # Option not found or invalid
                elif q.question_type == 'true_false':
                    # Assuming 'True'/'False' strings are stored in Option.text for correct option
                    if (answer_value == 'True' and q.options.filter(is_correct=True, text='True').exists()) or \
                       (answer_value == 'False' and q.options.filter(is_correct=True, text='False').exists()):
                        is_correct = True
                        self.score += q.score_points
                elif q.question_type == 'short_answer':
                    short_answer_text = answer_value
                    # For short answers, 'is_correct' is usually determined manually by a teacher.
                    # You might set it to False by default or based on some predefined keywords.
                    is_correct = False # Default, requires manual grading or advanced logic

                # Store data to create StudentAnswer instances later
                self.student_answers_data.append({
                    'question': q,
                    'selected_option': selected_option,
                    'short_answer_text': short_answer_text,
                    'is_correct': is_correct,
                })
            else:
                # If an answer is required but not provided, add an error
                self.add_error(field_name, "هذا الحقل مطلوب.")


        return cleaned_data

    def save_answers_and_update_test_result(self):
        """
        Saves student answers to the database and updates the TestResult.
        Call this method after form.is_valid() and form.save_answers_and_update_test_result().
        """
        if not hasattr(self, 'cleaned_data') or not self.is_valid():
            raise Exception("Form must be validated before saving answers.")
        if not self.test_result_instance:
            raise ValueError("TestResult instance is not set for this form.")

        # Clear existing answers for this test result if resubmission is allowed or to prevent duplicates
        # For a first submission, this won't do anything. For re-attempts, it might be relevant.
        self.test_result_instance.student_answers_detail.all().delete()

        for answer_data in self.student_answers_data:
            StudentAnswer.objects.create(
                test_result=self.test_result_instance,
                question=answer_data['question'],
                selected_option=answer_data['selected_option'],
                short_answer_text=answer_data['short_answer_text'],
                is_correct=answer_data['is_correct'],
            )

        # Update the TestResult instance
        self.test_result_instance.score = self.score
        self.test_result_instance.end_time = timezone.now()
        # You might set passed/failed based on a threshold here
        # For example:
        # if self.score >= self.test_result_instance.test.passing_score: # Assuming Test model has passing_score
        #    self.test_result_instance.passed = True
        # else:
        #    self.test_result_instance.passed = False
        self.test_result_instance.status = 'completed'
        self.test_result_instance.save()