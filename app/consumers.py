import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
import logging
from datetime import datetime
from .models import ChatMessage
from asgiref.sync import sync_to_async

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
User = get_user_model()  # Берём модель пользователя

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """🔌 Подключение клиента к WebSocket"""
        self.room_group_name = "global_chat"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logging.info(f"✅ Новый клиент подключился: {self.channel_name}")

    async def disconnect(self, close_code):
        """❌ Отключение клиента"""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        logging.info(f"❌ Клиент отключился: {self.channel_name}")

    async def receive(self, text_data):
        """📥 Прием сообщений от клиента"""
        try:
            data = json.loads(text_data)

            username = data.get("user", "Неизвестный")
            message = data.get("text", "")

            if not message:
                logging.warning(f"⚠️ [WS] Пустое сообщение: {data}")
                return

            logging.info(f"📥 [SERVER] Получено сообщение: {data}")

            # 🔍 Ищем пользователя в базе
            user = await sync_to_async(User.objects.get)(username=username)

            # 🕒 Создаём сообщение и сохраняем время
            chat_message = await sync_to_async(ChatMessage.objects.create)(
                user=user,
                text=message
            )

            created_at = chat_message.created_at.strftime("%Y-%m-%d %H:%M:%S") if chat_message else "Неизвестное время"

            # 📡 Рассылаем сообщение всем клиентам
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "username": username,
                    "message": message,
                    "created_at": created_at
                }
            )

        except User.DoesNotExist:
            logging.error(f"❌ Ошибка: Пользователь '{username}' не найден в базе!")
        except json.JSONDecodeError as e:
            logging.error(f"❌ Ошибка декодирования JSON: {str(e)}")
        except Exception as e:
            logging.error(f"❌ Ошибка при обработке сообщения: {str(e)}")


    async def chat_message(self, event):
        """📤 Отправка сообщения всем клиентам"""
        await self.send(text_data=json.dumps({
            "user": event["username"],
            "text": event["message"],
            "created_at": event["created_at"]
        }))