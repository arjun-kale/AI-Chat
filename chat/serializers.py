from rest_framework import serializers
from .models import Conversation, Message, Document


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'message_type', 'content', 'timestamp']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file', 'file_type', 'original_filename', 'uploaded_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Conversation
        fields = ['id', 'session_id', 'created_at', 'updated_at', 'messages', 'documents']


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000)
    session_id = serializers.CharField(max_length=100, required=False)


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    session_id = serializers.CharField(max_length=100, required=False)
