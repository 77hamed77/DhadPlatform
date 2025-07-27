from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q # لاستخدام عمليات OR في الاستعلامات
from .models import Conversation, Message
from .forms import MessageForm # سننشئ هذا النموذج لاحقاً
from django.contrib import messages
from core.models import User # استيراد نموذج المستخدم
from django.http import JsonResponse, HttpResponse # تأكد من استيراد JsonResponse
from django.core import serializers # لاستخدام serializing Objects to JSON
from django.utils import timezone
import json # لإدارة JSON في الـ AJAX

@login_required
def inbox(request):
    # جلب جميع المحادثات التي يكون المستخدم الحالي طرفاً فيها
    # وترتيبها حسب آخر تحديث
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')

    context = {
        'conversations': conversations
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def conversation_detail(request, conversation_id):
    # جلب المحادثة المحددة، أو إظهار خطأ 404 إذا لم يتم العثور عليها
    # والتأكد أن المستخدم الحالي هو أحد المشاركين فيها
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if not request.user in conversation.participants.all():
        # إذا لم يكن المستخدم مشاركاً في المحادثة، أعد توجيهه أو أظهر خطأ
        messages.error(request, 'لا تملك صلاحية الوصول لهذه المحادثة.')
        return redirect('inbox')

    messages_in_conversation = Message.objects.filter(conversation=conversation).order_by('timestamp')

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            # تحديث تاريخ آخر تحديث للمحادثة
            conversation.updated_at = message.timestamp
            conversation.save()

            # يمكن استخدام JsonResponse هنا إذا أردت تحديث الدردشة عبر AJAX
            # return JsonResponse({'status': 'success', 'message': message.content})
            return redirect('conversation_detail', conversation_id=conversation.id) # إعادة توجيه لتحديث الصفحة
        else:
            messages.error(request, 'لا يمكن إرسال الرسالة. يرجى مراجعة المحتوى.')
    else:
        form = MessageForm() # نموذج فارغ لرسالة جديدة

    context = {
        'conversation': conversation,
        'messages_in_conversation': messages_in_conversation,
        'form': form,
        'other_participant': conversation.get_other_participant(request.user) # لتسهيل عرض اسم الطرف الآخر
    }
    return render(request, 'messaging/conversation_detail.html', context)

# يمكن إضافة واجهة (View) لبدء محادثة جديدة هنا لاحقاً

@login_required
def start_or_get_conversation(request, other_user_id):
    other_user = get_object_or_404(User, id=other_user_id)

    if request.user == other_user:
        messages.error(request, "لا يمكنك بدء محادثة مع نفسك.")
        return redirect('dashboard')

    conversation = Conversation.objects.filter(
        Q(participant1=request.user, participant2=other_user) |
        Q(participant1=other_user, participant2=request.user)
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(participant1=request.user, participant2=other_user)

    # --------------------------------------------------------------------------
    # منطق جلب الرسائل الجديدة لطلبات الـ AJAX (Polling)
    # --------------------------------------------------------------------------
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'last_message_id' in request.GET:
        last_message_id = request.GET.get('last_message_id')
        try:
            new_messages = Message.objects.filter(
                conversation=conversation,
                id__gt=last_message_id
            ).order_by('timestamp')

            messages_data = []
            for msg in new_messages:
                messages_data.append({
                    'id': msg.id,
                    'sender_username': msg.sender.username,
                    'sender_full_name': msg.sender.full_name,
                    'content': msg.content,
                    'timestamp': msg.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    'is_from_me': msg.sender == request.user
                })

            return JsonResponse({'messages': messages_data})

        except ValueError:
            return JsonResponse({'error': 'Invalid last_message_id'}, status=400)

    # --------------------------------------------------------------------------
    # منطق إرسال رسالة (POST)
    # --------------------------------------------------------------------------
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()

            # إذا كان الطلب AJAX، أرجع JsonResponse بدلاً من إعادة التوجيه
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'message': {
                        'id': message.id,
                        'sender_username': message.sender.username,
                        'sender_full_name': message.sender.full_name,
                        'content': message.content,
                        'timestamp': message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        'is_from_me': message.sender == request.user
                    }
                })
            # إذا لم يكن الطلب AJAX، قم بإعادة التوجيه كما كان
            return redirect('start_or_get_conversation', other_user_id=other_user_id)
        else:
            # إذا كان هناك خطأ في النموذج وطلب AJAX، أرجع JsonResponse بالخطأ
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)

    # جلب جميع الرسائل للمحادثة (للتحميل الأولي للصفحة)
    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')

    context = {
        'conversation': conversation,
        'other_user': other_user,
        'messages': messages,
        'form': form,
    }
    return render(request, 'messaging/conversation_detail.html', context)