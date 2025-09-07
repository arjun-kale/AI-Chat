from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render
from django.http import JsonResponse
from .models import Conversation, Message, Document
from .serializers import (
    ConversationSerializer, 
    MessageSerializer, 
    DocumentSerializer,
    ChatRequestSerializer,
    FileUploadSerializer
)
from .ai_service import AIService
import os
import uuid


# Initialize AI service
ai_service = AIService()


def index(request):
    """Serve the main chat interface"""
    return render(request, 'chat/index.html')


@api_view(['POST'])
def start_conversation(request):
    """Start a new conversation"""
    session_id = ai_service.create_conversation()
    conversation = Conversation.objects.create(session_id=session_id)
    serializer = ConversationSerializer(conversation)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_conversation(request, session_id):
    """Get conversation by session ID"""
    try:
        conversation = Conversation.objects.get(session_id=session_id)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data)
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def send_message(request):
    """Send a message and get AI response"""
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    message = serializer.validated_data['message']
    session_id = serializer.validated_data.get('session_id')
    
    # Create new conversation if no session_id provided
    if not session_id:
        session_id = ai_service.create_conversation()
        conversation = Conversation.objects.create(session_id=session_id)
    else:
        try:
            conversation = Conversation.objects.get(session_id=session_id)
        except Conversation.DoesNotExist:
            conversation = Conversation.objects.create(session_id=session_id)
    
    # Save user message
    user_message = Message.objects.create(
        conversation=conversation,
        message_type='user',
        content=message
    )
    
    # Get chat history for context
    chat_history = list(conversation.messages.values('message_type', 'content').order_by('timestamp'))
    
    # Generate AI response
    ai_response = ai_service.generate_response(message, session_id, chat_history)
    
    # Save AI response
    ai_message = Message.objects.create(
        conversation=conversation,
        message_type='assistant',
        content=ai_response
    )
    
    # Return both messages
    user_serializer = MessageSerializer(user_message)
    ai_serializer = MessageSerializer(ai_message)
    
    return Response({
        'session_id': session_id,
        'user_message': user_serializer.data,
        'ai_message': ai_serializer.data
    })


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_file(request):
    """Upload and process a file"""
    serializer = FileUploadSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    file = serializer.validated_data['file']
    session_id = serializer.validated_data.get('session_id')
    
    # Create new conversation if no session_id provided
    if not session_id:
        session_id = ai_service.create_conversation()
        conversation = Conversation.objects.create(session_id=session_id)
    else:
        try:
            conversation = Conversation.objects.get(session_id=session_id)
        except Conversation.DoesNotExist:
            conversation = Conversation.objects.create(session_id=session_id)
    
    # Determine file type
    file_extension = file.name.split('.')[-1].lower()
    if file_extension == 'pdf':
        file_type = 'pdf'
    elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        file_type = 'image'
    else:
        return Response({'error': 'Unsupported file type'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Save document
    document = Document.objects.create(
        conversation=conversation,
        file=file,
        file_type=file_type,
        original_filename=file.name
    )
    
    # Process file content
    file_path = document.file.path
    processed_content = ""
    
    if file_type == 'pdf':
        processed_content = ai_service.process_pdf(file_path)
    elif file_type == 'image':
        processed_content = ai_service.process_image(file_path)
    
    # Update document with processed content
    document.processed_content = processed_content
    document.save()
    
    # Add to vector database
    if processed_content:
        ai_service.add_document_to_vectordb(
            processed_content, 
            str(document.id), 
            session_id
        )
    
    serializer = DocumentSerializer(document)
    return Response({
        'session_id': session_id,
        'document': serializer.data,
        'message': 'File uploaded and processed successfully'
    })


@api_view(['GET'])
def get_conversations(request):
    """Get all conversations"""
    conversations = Conversation.objects.all()
    serializer = ConversationSerializer(conversations, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
def delete_conversation(request, session_id):
    """Delete a conversation"""
    try:
        conversation = Conversation.objects.get(session_id=session_id)
        conversation.delete()
        return Response({'message': 'Conversation deleted successfully'})
    except Conversation.DoesNotExist:
        return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
