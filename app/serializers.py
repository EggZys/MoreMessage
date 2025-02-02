from rest_framework import serializers
from .models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username')  # Добавьте это
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'text', 'created_at']