from .models import ChatMessage
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("🔌 [WebSocket] Клиент подключился!")
        await self.accept()
        await self.channel_layer.group_add("chat", self.channel_name)

    async def disconnect(self, close_code):
        print("❌ [WebSocket] Клиент отключился!")
        await self.channel_layer.group_discard("chat", self.channel_name)

    async def receive(self, text_data):
        """Получаем сообщение и рассылаем всем пользователям"""
        print(f"📥 [WebSocket] Получено сообщение: {text_data}")
        data = json.loads(text_data)
        username = data.get("user")
        message = data.get("text")

        user = await User.objects.filter(username=username).afirst()
        if user:
            await ChatMessage.objects.acreate(user=user, text=message)  # Сохраняем в БД

        await self.channel_layer.group_send(
            "chat",
            {
                "type": "chat_message",
                "user": username,
                "text": message,
            },
        )

    async def chat_message(self, event):
        """Отправляем сообщение всем клиентам"""
        print(f"📡 [WebSocket] Рассылаем сообщение: {event}")
        await self.send(text_data=json.dumps(event))
