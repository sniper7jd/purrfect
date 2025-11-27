"""Chat views."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Conversation, Message

User = get_user_model()


@login_required
def inbox(request):
    """List all conversations."""
    conversations = Conversation.objects.filter(
        participants=request.user
    ).annotate(
        last_message_time=Max('messages__sent_at')
    ).order_by('-last_message_time')
    
    # Add unread count to each conversation
    conversation_data = []
    for conv in conversations:
        other_user = conv.get_other_participant(request.user)
        unread_count = conv.messages.filter(read_at__isnull=True).exclude(sender=request.user).count()
        conversation_data.append({
            'conversation': conv,
            'other_user': other_user,
            'unread_count': unread_count,
            'last_message': conv.last_message,
        })
    
    return render(request, 'chat/inbox.html', {
        'conversations': conversation_data,
    })


@login_required
def conversation(request, conversation_id):
    """View a conversation."""
    conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
    other_user = conv.get_other_participant(request.user)
    messages = conv.messages.select_related('sender').all()
    
    # Mark messages as read
    conv.messages.filter(read_at__isnull=True).exclude(sender=request.user).update(
        read_at=timezone.now()
    )
    
    return render(request, 'chat/conversation.html', {
        'conversation': conv,
        'other_user': other_user,
        'messages': messages,
    })


@login_required
def start_conversation(request, user_id):
    """Start a new conversation with a user."""
    other_user = get_object_or_404(User, pk=user_id)
    
    if other_user == request.user:
        return redirect('chat:inbox')
    
    # Check if conversation already exists
    existing = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if existing:
        return redirect('chat:conversation', conversation_id=existing.id)
    
    # Create new conversation
    conv = Conversation.objects.create()
    conv.participants.add(request.user, other_user)
    
    return redirect('chat:conversation', conversation_id=conv.id)


@login_required
def get_messages(request, conversation_id):
    """API endpoint to get messages (for polling fallback)."""
    conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
    
    after = request.GET.get('after')
    messages_qs = conv.messages.select_related('sender')
    
    if after:
        messages_qs = messages_qs.filter(id__gt=after)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender_id': msg.sender_id,
        'sender_username': msg.sender.username,
        'sent_at': msg.sent_at.isoformat(),
        'is_mine': msg.sender_id == request.user.id,
    } for msg in messages_qs]
    
    return JsonResponse({'messages': messages_data})


@login_required
def send_message(request, conversation_id):
    """API endpoint to send message (for fallback without WebSocket)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    
    conv = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({'error': 'Content required'}, status=400)
    
    message = Message.objects.create(
        conversation=conv,
        sender=request.user,
        content=content
    )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender_id,
            'sent_at': message.sent_at.isoformat(),
        }
    })



