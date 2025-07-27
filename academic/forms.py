from django import forms
from .models import Submission, Question, Option, TestResult # استيراد نماذج الاختبارات
from collections import OrderedDict # للحفاظ على ترتيب حقول النموذج


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
        self.questions = kwargs.pop('questions') # نمرر قائمة كائنات Question هنا
        self.test_instance_id = kwargs.pop('test_instance_id', None) # لتحديد أي اختبار هذا
        super().__init__(*args, **kwargs)

        # ترتيب حقول النموذج بناءً على ترتيب الأسئلة
        self.fields = OrderedDict()

        for q in self.questions:
            field_name = f'question_{q.id}'
            if q.question_type == 'multiple_choice':
                choices = [(str(option.id), option.text) for option in q.options.all()]
                self.fields[field_name] = forms.ChoiceField(
                    label=q.text,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-radio'}), # تم التعديل هنا: إضافة 'form-radio'
                    required=True
                )
            elif q.question_type == 'true_false':
                choices = [('True', 'صحيح'), ('False', 'خطأ')]
                self.fields[field_name] = forms.ChoiceField(
                    label=q.text,
                    choices=choices,
                    widget=forms.RadioSelect(attrs={'class': 'form-radio'}), # تم التعديل هنا: إضافة 'form-radio'
                    required=True
                )
            elif q.question_type == 'short_answer':
                self.fields[field_name] = forms.CharField(
                    label=q.text,
                    widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-input'}), # تم التعديل هنا: إضافة 'form-input'
                    required=True
                )
            # يمكنك إضافة أنواع أسئلة أخرى هنا

        # إضافة حقل مخفي لتمرير معرف الاختبار
        if self.test_instance_id:
            self.fields['test_instance_id'] = forms.CharField(widget=forms.HiddenInput(), initial=self.test_instance_id)

    # دالة للتحقق من الإجابات وحساب الدرجة
    def clean(self):
        cleaned_data = super().clean()
        self.score = 0
        self.student_answers = {}

        for q in self.questions:
            field_name = f'question_{q.id}'
            answer = cleaned_data.get(field_name)
            self.student_answers[q.id] = answer # تخزين إجابة الطالب

            if answer is not None:
                if q.question_type == 'multiple_choice':
                    try:
                        selected_option = Option.objects.get(id=int(answer))
                        if selected_option.is_correct:
                            self.score += q.score_points
                    except Option.DoesNotExist:
                        pass # الخيار غير موجود
                elif q.question_type == 'true_false':
                    if (answer == 'True' and q.options.filter(is_correct=True, text='True').exists()) or \
                       (answer == 'False' and q.options.filter(is_correct=True, text='False').exists()):
                        self.score += q.score_points
                # For 'short_answer', scoring would typically be manual by a teacher
                # You might want to save these answers for later review.
        return cleaned_data