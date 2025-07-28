# messaging/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q # مهم جداً لاستخدام OR في الفلترة
from .models import Conversation, Message
from .forms import MessageForm
from core.models import User # تأكد من أن هذا الاستيراد صحيح لنموذج المستخدم الخاص بك

@login_required
def inbox(request):
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    for conv in conversations:
        conv.other_participant = conv.get_other_participant(request.user)
    context = {
        'conversations': conversations,
    }
    return render(request, 'messaging/inbox.html', context)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        return redirect('messaging:inbox')

    messages = conversation.messages.all().order_by('timestamp')
    form = MessageForm()
    other_user = conversation.get_other_participant(request.user)

    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)

    context = {
        'conversation': conversation,
        'conversation_messages': messages,
        'form': form,
        'other_user': other_user,
    }
    return render(request, 'messaging/conversation_detail.html', context)

@login_required
def start_or_get_conversation(request, other_user_id):
    other_user = get_object_or_404(User, id=other_user_id)
    if request.user == other_user:
        return redirect('messaging:inbox')

    conversation = Conversation.objects.filter(
        conversation_type='private',
        participants=request.user
    ).filter(
        participants=other_user
    ).first()

    if not conversation:
        conversation = Conversation.objects.create(conversation_type='private')
        conversation.participants.add(request.user, other_user)
        conversation.save()

    return redirect('messaging:conversation_detail', conversation_id=conversation.id)

@login_required
def new_conversation_selection(request):
    """
    يعرض قائمة بالمعلمين والمسؤولين الذين يمكن للطالب بدء محادثة معهم.
    """
    # جلب جميع المعلمين والمسؤولين
    # استبعاد المستخدم الحالي من القائمة لمنعه من الدردشة مع نفسه
    # وفلترة الأدوار
    # ******** التعديل الرئيسي هنا: استخدام 'first_name', 'last_name' للترتيب ********
    teachers = User.objects.filter(role='teacher').exclude(id=request.user.id).order_by('first_name', 'last_name', 'username')
    admins = User.objects.filter(role='admin').exclude(id=request.user.id).order_by('first_name', 'last_name', 'username')

    search_query = request.GET.get('q')
    if search_query:
        # تطبيق البحث على كل من المعلمين والمسؤولين بشكل منفصل
        # ******** التعديل الرئيسي هنا: استخدام 'first_name', 'last_name' في Q object للبحث ********
        teachers = teachers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
        admins = admins.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    context = {
        'teachers': teachers,
        'admins': admins,
        'search_query': search_query,
    }
    return render(request, 'messaging/new_conversation_selection.html', context)