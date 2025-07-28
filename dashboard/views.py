# dashboard/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import JsonResponse
from core.models import User 
from registration.models import RegistrationRequest 
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger 
from django.utils import timezone 
from django.contrib import messages 
# من الآن فصاعدًا، لن نحتاج إلى send_mail أو ما شابهها هنا
# from django.core.mail import send_mail 
# from django.conf import settings 
# from django.template.loader import render_to_string 
# from django.utils.html import strip_tags 
import string
import random

def is_admin_or_staff(user):
    return user.is_staff or user.is_superuser

@login_required 
@user_passes_test(is_admin_or_staff) 
def admin_dashboard(request):
    total_users = User.objects.count()
    pending_requests = RegistrationRequest.objects.filter(status='pending').count()
    approved_requests = RegistrationRequest.objects.filter(status='approved').count()

    all_requests = RegistrationRequest.objects.order_by('-created_at')

    paginator = Paginator(all_requests, 10)

    page_number = request.GET.get('page')
    try:
        recent_requests = paginator.page(page_number)
    except PageNotAnInteger:
        recent_requests = paginator.page(1)
    except EmptyPage:
        recent_requests = paginator.page(paginator.num_pages)

    context = {
        'total_users': total_users,
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'recent_requests': recent_requests, 
        'paginator': paginator, 
    }
    return render(request, 'dashboard/admin_dashboard.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def user_data_api(request):
    gender_data = User.objects.values('gender').annotate(count=Count('gender'))
    
    gender_counts = {'male': 0, 'female': 0}
    for item in gender_data:
        if item['gender'] == 'male':
            gender_counts['male'] = item['count']
        elif item['gender'] == 'female':
            gender_counts['female'] = item['count']

    status_data = RegistrationRequest.objects.values('status').annotate(count=Count('status'))
    
    status_counts = {'pending': 0, 'approved': 0, 'rejected': 0}
    for item in status_data:
        status_counts[item['status']] = item['count']

    data = {
        'gender_counts': gender_counts,
        'status_counts': status_counts,
        'total_users': User.objects.count() 
    }
    
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin_or_staff)
def approve_registration_request(request, request_id):
    if request.method == 'POST':
        registration_request = get_object_or_404(RegistrationRequest, pk=request_id)

        if registration_request.status == 'approved':
            messages.warning(request, f'طلب التسجيل من {registration_request.full_name} تمت الموافقة عليه مسبقاً.')
            return JsonResponse({'status': 'warning', 'message': f'طلب التسجيل من {registration_request.full_name} تمت الموافقة عليه مسبقاً.'})

        try:
            if User.objects.filter(email=registration_request.email).exists():
                messages.error(request, f'فشل إنشاء حساب للطالب {registration_request.full_name}: يوجد مستخدم بالفعل بهذا البريد الإلكتروني ({registration_request.email}).')
                return JsonResponse({'status': 'error', 'message': f'فشل إنشاء حساب للطالب {registration_request.full_name}: يوجد مستخدم بالفعل بهذا البريد الإلكتروني ({registration_request.email}).'})
            
            # الحصول على كلمة المرور من بيانات POST إذا كانت موجودة (من زر التوليد اليدوي)
            # أو توليد واحدة عشوائية إذا لم يتم توفيرها.
            generated_password = request.POST.get('generated_password')
            if not generated_password:
                # إذا لم يتم توليدها بواسطة الزر، قم بتوليدها هنا بشكل تلقائي
                generated_password = User.objects.make_random_password(length=12, 
                                                                       allowed_chars=string.ascii_letters + string.digits + string.punctuation)


            # إنشاء كائن User جديد
            user = User(
                username=registration_request.email, 
                email=registration_request.email,
                role='student', 
                is_active=True, 
                first_name=registration_request.full_name.split(' ')[0] if registration_request.full_name else '',
                last_name=' '.join(registration_request.full_name.split(' ')[1:]) if registration_request.full_name and len(registration_request.full_name.split(' ')) > 1 else '',
                phone_number=registration_request.whatsapp_number,
                country=registration_request.country,
            )
            
            # تعيين كلمة المرور المشفرة (باستخدام set_password لضمان التشفير الصحيح)
            user.set_password(generated_password)
            user.save()

            # تحديث حالة طلب التسجيل إلى "approved"
            registration_request.status = 'approved'
            registration_request.approved_at = timezone.now() 
            registration_request.user = user 
            registration_request.save()
            
            # لا يوجد إرسال بريد إلكتروني تلقائي للطالب هنا

            messages.success(request, f'تمت الموافقة على طلب {registration_request.full_name} وتم إنشاء حسابه بنجاح. كلمة المرور التي تم إنشاؤها: "{generated_password}"')
            return JsonResponse({
                'status': 'success', 
                'message': f'تمت الموافقة على طلب {registration_request.full_name} وتم إنشاء حسابه بنجاح.',
                'user_username': user.username, 
                'user_pk': user.pk,
                'generated_password': generated_password # إرجاع كلمة المرور للإدارة لعرضها
            })

        except Exception as e:
            messages.error(request, f'فشل في الموافقة على طلب {registration_request.full_name}: {e}')
            return JsonResponse({'status': 'error', 'message': f'فشل في الموافقة على الطلب: {str(e)}'}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'طريقة غير مسموح بها.'}, status=405)


@login_required
@user_passes_test(is_admin_or_staff)
def reject_registration_request(request, request_id):
    if request.method == 'POST':
        registration_request = get_object_or_404(RegistrationRequest, pk=request_id)
        
        if registration_request.status == 'approved':
             messages.warning(request, f'لا يمكن رفض طلب {registration_request.full_name} لأنه تمت الموافقة عليه مسبقاً.')
             return JsonResponse({'status': 'warning', 'message': f'لا يمكن رفض طلب {registration_request.full_name} لأنه تمت الموافقة عليه مسبقاً.'})

        if registration_request.status == 'rejected':
             messages.warning(request, f'طلب {registration_request.full_name} مرفوض مسبقاً.')
             return JsonResponse({'status': 'warning', 'message': f'طلب {registration_request.full_name} مرفوض مسبقاً.'})

        try:
            registration_request.status = 'rejected'
            registration_request.save()
            
            messages.info(request, f'تم رفض طلب {registration_request.full_name}.')
            return JsonResponse({'status': 'success', 'message': f'تم رفض طلب {registration_request.full_name}.'})

        except Exception as e:
            messages.error(request, f'فشل في رفض طلب {registration_request.full_name}: {e}')
            return JsonResponse({'status': 'error', 'message': f'فشل في رفض الطلب: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'طريقة غير مسموح بها.'}, status=405)


# دالة جديدة لتوليد كلمة مرور عشوائية (ستُستدعى عبر AJAX)
@login_required
@user_passes_test(is_admin_or_staff)
def generate_random_password_api(request):
    if request.method == 'GET': # أو يمكنك استخدام POST إذا أردت إرسال أي بيانات
        # يمكنك تخصيص طول الأحرف ونوعها هنا
        length = 12
        chars = string.ascii_letters + string.digits + string.punctuation
        random_password = ''.join(random.choice(chars) for i in range(length))
        return JsonResponse({'password': random_password})
    return JsonResponse({'status': 'error', 'message': 'طريقة غير مسموح بها.'}, status=405)