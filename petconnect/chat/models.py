"""Chat models for real-time messaging."""
from django.db import models
from django.conf import settings
from django.utils import timezone


class Conversation(models.Model):
    """Conversation between two users."""
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='conversations')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation {self.id}"

    @property
    def last_message(self):
        return self.messages.order_by('-sent_at').first()

    def get_other_participant(self, user):
        """Get the other participant in the conversation."""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    """Individual message in a conversation."""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages_sent')
    content = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'messages'
        ordering = ['sent_at']

    def __str__(self):
        return f"Message from {self.sender.username} at {self.sent_at}"

    @property
    def is_read(self):
        return self.read_at is not None

    def mark_as_read(self):
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=['read_at'])

