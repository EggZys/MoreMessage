from rest_framework import serializers
from .models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())  # ✅ Автоматически устанавливает user

    class Meta:
        model = ChatMessage
        fields = ['id', 'user', 'text', 'created_at']
