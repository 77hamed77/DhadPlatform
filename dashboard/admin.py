# dashboard/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.http import JsonResponse
from core.models import User
from registration.models import RegistrationRequest
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.contrib import messages # لاستخدام رسائل Django
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import json # لاستقبال بيانات JSON في طلبات AJAX

# دالة للتحقق مما إذا كان المستخدم مديراً (superadmin أو لديه صلاحيات خاصة)
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
    except PageNotIsNotInteger:
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
    }
    return JsonResponse(data)


@login_required
@user_passes_test(is_admin_or_staff)
def approve_registration_request(request, request_id):
    if request.method == 'POST':
        registration_request = get_object_or_404(RegistrationRequest, pk=request_id)

        if registration_request.status == 'approved':
            # return JsonResponse({'status': 'warning', 'message': 'تمت الموافقة على هذا الطلب مسبقاً.'}, status=200)
            messages.warning(request, f'طلب التسجيل من {registration_request.full_name} تمت الموافقة عليه مسبقاً.')
            return JsonResponse({'status': 'warning', 'message': f'طلب التسجيل من {registration_request.full_name} تمت الموافقة عليه مسبقاً.'})


        try:
            # التحقق مما إذا كان هناك مستخدم بنفس البريد الإلكتروني بالفعل
            if User.objects.filter(email=registration_request.email).exists():
                messages.error(request, f'فشل إنشاء حساب للطالب {registration_request.full_name}: يوجد مستخدم بالفعل بهذا البريد الإلكتروني ({registration_request.email}).')
                # return JsonResponse({'status': 'error', 'message': 'يوجد مستخدم بالفعل بهذا البريد الإلكتروني.'}, status=400)
                return JsonResponse({'status': 'error', 'message': f'فشل إنشاء حساب للطالب {registration_request.full_name}: يوجد مستخدم بالفعل بهذا البريد الإلكتروني ({registration_request.email}).'})


            # إنشاء كائن User جديد
            user = User(
                username=registration_request.email, # عادة ما يكون البريد الإلكتروني هو اسم المستخدم
                email=registration_request.email,
                role='student', # تعيين الدور كـ "student"
                is_active=True,
                first_name=registration_request.full_name.split(' ')[0] if registration_request.full_name else '',
                last_name=' '.join(registration_request.full_name.split(' ')[1:]) if registration_request.full_name and len(registration_request.full_name.split(' ')) > 1 else '',
                phone_number=registration_request.whatsapp_number,
                country=registration_request.country,
            )
            # تعيين كلمة المرور المشفرة
            user.password = registration_request.password_hash
            user.save()

            # تحديث حالة طلب التسجيل
            registration_request.status = 'approved'
            registration_request.approved_at = timezone.now()
            registration_request.user = user # ربط المستخدم بطلب التسجيل
            registration_request.save()

            # إرسال بريد إلكتروني للطالب
            subject = 'تمت الموافقة على طلب تسجيلك في منصة ضاد التعليمية!'
            html_message = render_to_string('registration/approved_student_email.html', {
                'student_name': registration_request.full_name,
                'email': registration_request.email,
                'login_link': request.build_absolute_uri('/login/') # تأكد من أن هذا المسار صحيح
            })
            plain_message = strip_tags(html_message)
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [registration_request.email]

            send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message, fail_silently=False)
            
            messages.success(request, f'تمت الموافقة على طلب {registration_request.full_name} وتم إنشاء حسابه بنجاح.')
            return JsonResponse({'status': 'success', 'message': f'تمت الموافقة على طلب {registration_request.full_name} وتم إنشاء حسابه بنجاح.'})

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
            
            # يمكنك اختيار إرسال بريد إلكتروني لإبلاغ الطالب بالرفض هنا
            # subject = 'بخصوص طلب تسجيلك في منصة ضاد التعليمية'
            # html_message = render_to_string('registration/rejected_student_email.html', {
            #     'student_name': registration_request.full_name,
            # })
            # plain_message = strip_tags(html_message)
            # from_email = settings.DEFAULT_FROM_EMAIL
            # recipient_list = [registration_request.email]
            # send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message, fail_silently=False)

            messages.info(request, f'تم رفض طلب {registration_request.full_name}.')
            return JsonResponse({'status': 'success', 'message': f'تم رفض طلب {registration_request.full_name}.'})

        except Exception as e:
            messages.error(request, f'فشل في رفض طلب {registration_request.full_name}: {e}')
            return JsonResponse({'status': 'error', 'message': f'فشل في رفض الطلب: {str(e)}'}, status=500)

    return JsonResponse({'status': 'error', 'message': 'طريقة غير مسموح بها.'}, status=405)