from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    """Model to store chat conversations"""
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']


class Message(models.Model):
    """Model to store individual messages in a conversation"""
    MESSAGE_TYPES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['timestamp']


class Document(models.Model):
    """Model to store uploaded documents"""
    DOCUMENT_TYPES = [
        ('pdf', 'PDF'),
        ('image', 'Image'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    file = models.FileField(upload_to='documents/')
    file_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES)
    original_filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed_content = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-uploaded_at']
