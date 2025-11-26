"""WebSocket consumers for real-time chat."""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for chat functionality."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Verify user is participant
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Mark unread messages as read
        await self.mark_messages_read()
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Handle incoming WebSocket message."""
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            content = data.get('content', '').strip()
            if content:
                # Save message to database
                message = await self.save_message(content)
                
                # Broadcast to room
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': {
                            'id': message.id,
                            'content': message.content,
                            'sender_id': self.user.id,
                            'sender_username': self.user.username,
                            'sender_avatar': self.user.profile_picture.url if self.user.profile_picture else None,
                            'sent_at': message.sent_at.isoformat(),
                        }
                    }
                )
        
        elif message_type == 'typing':
            # Broadcast typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'is_typing': data.get('is_typing', False)
                }
            )
        
        elif message_type == 'read':
            await self.mark_messages_read()
    
    async def chat_message(self, event):
        """Send message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket."""
        # Don't send to the user who is typing
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    @database_sync_to_async
    def check_participant(self):
        """Check if user is participant in conversation."""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database."""
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )
        conversation.updated_at = timezone.now()
        conversation.save(update_fields=['updated_at'])
        return message
    
    @database_sync_to_async
    def mark_messages_read(self):
        """Mark all messages from other user as read."""
        Message.objects.filter(
            conversation_id=self.conversation_id,
            read_at__isnull=True
        ).exclude(sender=self.user).update(read_at=timezone.now())



