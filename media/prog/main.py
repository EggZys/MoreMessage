import flet as ft
from flet import alignment
import requests
import json
import re
import time
import logging
from passlib.hash import django_pbkdf2_sha256
import datetime
import socket
import websockets
import asyncio
from crypter import cipher, uncipher
import os


hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Конфигурация
CREDENTIALS_FILE = "data/user_credentials.json"
MAX_LOGIN_ATTEMPTS = 3
BLOCK_TIME = 10

class ChatInterface:
    def __init__(self, page, username, theme_mode, language, auth_token):
        self.page = page
        self.username = username
        self.theme_mode = theme_mode
        self.language = language
        self.auth_token = auth_token
        self.messages = []
        self.ws = None  # WebSocket клиент
        self.page.on_keyboard_event = self.handle_keyboard_event
        self.reply_to_message = None  # Новое поле для хранения сообщения-оригинала
        self.selected_message = None  # Для контекстного меню
        self.initialize_ui()

        asyncio.run(self.connect_websocket())
    
    async def connect_websocket(self):
        try:
            self.ws = await websockets.connect("ws://127.0.0.1:8000/ws/chat/")
            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                
                # Дешифруем сообщение
                if 'text' in data:
                    data['text'] = uncipher(data['text'], mu=1)
                
                # Преобразуем строку created_at в datetime
                if isinstance(data.get("created_at"), str):
                    try:
                        data["created_at"] = datetime.datetime.fromisoformat(
                            data["created_at"].replace('Z', '+00:00')
                        )
                    except ValueError as e:
                        data["created_at"] = datetime.datetime.now()
                        logging.error(f"Ошибка преобразования даты в WebSocket: {e}")
                
                self.messages.append(data)
                self.update_chat_display()
        except Exception as e:
            print(f"❌ WebSocket ошибка: {e}")

    def load_user_data(self):
        """Загрузка реальных данных пользователя с сервера"""
        try:
            response = requests.get("http://127.0.0.1:8000/api/users/")
            if response.status_code == 200:
                data = response.json()
                # Парсим строку с пользователями
                users = json.loads(data["users"]) 
                
                # Ищем текущего пользователя
                for user in users:
                    if user["fields"]["username"] == self.username:
                        return {
                            "username": user["fields"]["username"],
                            "email": user["fields"]["email"] or "не указано",
                            "avatar": "👤"
                        }
                return self.default_user_data()
            
            logging.error(f"Ошибка API: {response.status_code}")
            return self.default_user_data()
            
        except Exception as e:
            logging.error(f"Ошибка подключения: {str(e)}")
            return self.default_user_data()

    def default_user_data(self):
        """Данные пользователя по умолчанию"""
        return {
            "username": self.username,
            "email": "неизвестно@email.com",
            "avatar": "👤"
        }

    def initialize_ui(self):
        # Обновленная цветовая схема из CSS
        self.page.title = self.translate("Global Chat")
        self.bg_color = "#18181B" if self.theme_mode == ft.ThemeMode.DARK else "#F4F4F5"
        self.text_color = "#F4F4F5" if self.theme_mode == ft.ThemeMode.DARK else "#18181B"
        self.primary_color = "#6366F1"
        self.secondary_color = "#EC4899"

        self.gradient = ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=["#6366F1", "#EC4899"]
        )
        
        # Цветовая схема
        self.bg_color = ft.Colors.BLUE_GREY_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_100
        self.text_color = ft.Colors.WHITE if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.BLACK
        self.primary_color = ft.Colors.BLUE_ACCENT_700
        
        # Верхняя панель с профилем
        self.profile_button = ft.IconButton(
            icon=ft.Icons.ACCOUNT_CIRCLE,
            icon_size=40,
            icon_color=self.primary_color,
            on_click=self.show_profile_modal
        )
        
        self.header = ft.Row(
            [
                ft.Text(
                    self.translate("Глобальный чат"), 
                    size=28, 
                    weight=ft.FontWeight.BOLD,
                    color=self.primary_color
                ),
                self.profile_button
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        # Область сообщений
        self.chat_messages = ft.ListView(
            expand=True,
            spacing=15,
            padding=15,
            auto_scroll=True
        )
        
        # Поле ввода сообщения
        self.new_message_field = ft.TextField(
            label=self.translate("Напишите сообщение..."),
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=3,  # Уменьшено с 5
            border_radius=15,
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            bgcolor=ft.Colors.with_opacity(0.05, self.primary_color),
            cursor_color=self.primary_color,
            content_padding=10,  # Уменьшено
        )

        # Обновить стили кнопок:
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_size=24,
            icon_color=ft.Colors.WHITE,
            tooltip=self.translate("Отправить"),
            bgcolor=self.primary_color,
            width=40,
            height=40,
            on_click=self.send_message,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=10,
                overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
            )
        )   

        
        # Сборка интерфейса
        self.page.add(
            self.header,
            ft.Container(
                content=self.chat_messages,
                border=ft.border.all(2, self.primary_color),
                border_radius=20,
                padding=20,
                expand=True,
                bgcolor=self.bg_color,
                shadow=ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=15,
                    color=ft.Colors.BLACK if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_400,
                )
            ),
            ft.Container(
                content=ft.Row(
                    [
                        self.new_message_field,
                        ft.Container(self.send_button, padding=ft.padding.only(left=10))
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10
                ),
                padding=15,
                bgcolor=self.bg_color,
                border_radius=15,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=10,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
                )
            )
        )
        
        self.load_messages()
        self.page.update()

    def handle_keyboard_event(self, e: ft.KeyboardEvent):
        """Обработка сочетаний клавиш"""
        if e.key == "Enter" and e.shift:
            self.send_message(e)
            self.page.update()
        elif e.key == "Enter" and not e.shift:
            current_value = self.new_message_field.value
            self.new_message_field.value = f"{current_value}\n"
            self.new_message_field.update()

    def show_profile_modal(self, e):
        """Обновляем модальное окно с актуальными данными"""
        # При каждом открытии обновляем данные
        self.user_data = self.load_user_data() 
        
        profile_content = ft.Column([
            ft.ListTile(
                leading=ft.Text(self.user_data["avatar"], size=32),
                title=ft.Text(
                    self.user_data["username"], 
                    weight=ft.FontWeight.BOLD,
                    color=self.primary_color
                ),
                subtitle=ft.Text(
                    self.user_data["email"],
                    style=ft.TextStyle(color=ft.Colors.GREY)
                ),
            ),
            ft.Divider(),
            ft.ElevatedButton(
                text=self.translate("Настройки"),
                icon=ft.Icons.SETTINGS,
                on_click=self.show_settings_modal,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=15
                )
            )
        ], tight=True)
        
        self.profile_modal = ft.AlertDialog(
            title=ft.Text(self.translate("Профиль")),
            content=profile_content,
            shape=ft.RoundedRectangleBorder(radius=20)
        )
        
        self.page.dialog = self.profile_modal
        self.profile_modal.open = True
        self.page.update()

    def show_settings_modal(self, e):
        """Модальное окно настроек"""
        theme_switch = ft.Switch(
            label=self.translate("Темная тема"),
            value=self.theme_mode == ft.ThemeMode.DARK,
            on_change=self.toggle_theme
        )
        
        language_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("ru", "Русский"),
                ft.dropdown.Option("en", "English")
            ],
            value=self.language,
            width=120,
            on_change=self.change_language
        )
        
        settings_content = ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.COLOR_LENS),
                title=ft.Text(self.translate("Тема")),
                trailing=theme_switch,
            ),
            ft.ListTile(
                leading=ft.Icon(ft.Icons.LANGUAGE),
                title=ft.Text(self.translate("Язык")),
                trailing=language_dropdown,
            )
        ], spacing=15)
        
        self.settings_modal = ft.AlertDialog(
            title=ft.Text(self.translate("Настройки")),
            content=settings_content,
            shape=ft.RoundedRectangleBorder(radius=20)
        )
        
        self.page.dialog = self.settings_modal
        self.settings_modal.open = True
        self.page.update()

    def toggle_theme(self, e):
        self.theme_mode = ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT
        self.page.theme_mode = self.theme_mode
        self.page.update()
        self.initialize_ui()  # Переинициализация для применения темы

    def change_language(self, e):
        current_messages = self.messages.copy()
        self.language = e.control.value
        self.page.update()
        self.initialize_ui()
        self.messages = current_messages
        self.update_chat_display()  # Переинициализация для применения языка

    def translate(self, text):
        """Локализация с учетом переданного языка"""
        return AuthApp.translate_static(self.language, text)

    def send_message(self, e):
        message = self.new_message_field.value.strip()
        if not message:
            return

        # Добавляем информацию об ответе
        encrypted_msg = cipher(message)
        data = {
            "user": self.username,
            "text": encrypted_msg,
            "created_at": datetime.datetime.now().isoformat(),
            "reply_to": self.reply_to_message["id"] if self.reply_to_message else None
        }

        logging.info(f"📤 [CLIENT] Отправка WebSocket-сообщения: {data}")

        if self.ws:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.ws.send(json.dumps(data)))  # ✅ Работает в активном event loop
                else:
                    asyncio.run(self.ws.send(json.dumps(data)))  # Используется только если event loop не запущен
            except RuntimeError:
                asyncio.run(self.ws.send(json.dumps(data)))  # Если event loop отсутствует, создаём новый

        # 🧹 Очищаем поле ввода
        self.new_message_field.value = ""
        if self.reply_to_message:
            self.clear_reply(None)
        self.page.update()

    def load_messages(self):
        try:
            headers = {
                "Authorization": f"Token {self.auth_token}",
                "Content-Type": "application/json"
            }
            response = requests.get("http://127.0.0.1:8000/api/messages/", headers=headers)
            if response.status_code == 200:
                messages_data = response.json()
                self.messages = []  # Очистка перед загрузкой
                for msg in messages_data:
                    user_response = requests.get(
                        f"http://127.0.0.1:8000/api/users/{msg['user']}/",
                        headers=headers
                    )
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        username = user_data.get('username', 'unknown')
                    else:
                        username = "unknown"  # Обработка ошибки

                    try:
                        created_at = datetime.datetime.fromisoformat(msg['created_at'].replace('Z', '+00:00'))
                    except (ValueError, KeyError):
                        print("⚠️ Ошибка даты, ставлю текущее время")
                        created_at = datetime.datetime.now()

                    self.messages.append({
                        "id": msg['id'],  # Добавляем ID сообщения
                        "user": username,
                        "text": uncipher(msg['text'], mu=1),
                        "created_at": created_at,
                        "reply_to": msg.get('reply_to')  # Добавляем информацию об ответе
                    })

                self.messages.sort(key=lambda x: x['created_at'])  # Сортировка по datetime
                self.update_chat_display()  # Обновление отображения
            else:
                logging.error(f"Ошибка при загрузке сообщений: {response.status_code}")

        except Exception as e:
            logging.error(f"Ошибка загрузки сообщений: {str(e)}")

    def update_chat_display(self):
        """Обновление отображения сообщений с группировкой."""
        sorted_messages = self.messages
        controls = []
        last_date = None
        last_user = None
        message_group = []

        month_names = {
            1: "января", 2: "февраля", 3: "марта", 4: "апреля",
            5: "мая", 6: "июня", 7: "июля", 8: "августа",
            9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
        }

        for msg in sorted_messages:
            print(f"Сырые данные: {msg}")
            # Добавляем 3 часа к времени
            dt = msg["created_at"] + datetime.timedelta(hours=3)

            current_date = dt.date()

            if last_date != current_date:
                if message_group:
                    controls.append(self.create_message_group(message_group, last_user))
                    message_group = []

                date_text = f"{dt.day} {month_names[dt.month]} {dt.year} г."
                controls.append(
                    ft.Container(
                        content=ft.Text(date_text, color=ft.Colors.GREY_600, size=12),
                        alignment=ft.alignment.center,
                        padding=10
                    )
                )
                last_date = current_date

            if msg["user"] != last_user and message_group:
                controls.append(self.create_message_group(message_group, last_user))
                message_group = []

            message_group.append(msg)
            last_user = msg["user"]

        if message_group:
            controls.append(self.create_message_group(message_group, last_user))

        self.chat_messages.controls = controls
        self.page.update()

        # Прокрутка к последнему сообщению после обновления
        self.chat_messages.scroll_to(offset=0, duration=0.1)
    
    def create_message_bubble(self, message: dict):
        is_my_message = message["user"] == self.username
        adjusted_time = (message["created_at"] + datetime.timedelta(hours=3)).strftime("%H:%M")

        # Контейнер времени
        time_label = ft.Text(
            adjusted_time,
            color=ft.Colors.GREY_600,
            size=12,
            opacity=1.0,  # Теперь ВСЕГДА видно
        )

        # Основной контейнер сообщения
        message_row = ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"{message['user']}",
                            size=12,
                            color=self.primary_color if is_my_message else ft.Colors.GREY_600,
                        ),
                        ft.Text(
                            message["text"],
                            size=16,
                            color=ft.Colors.WHITE if is_my_message else ft.Colors.BLACK,
                        ),
                        time_label  # Просто вставляем время сразу
                    ], spacing=5),
                    bgcolor=self.primary_color if is_my_message else self.secondary_color,
                    padding=15,
                    border_radius=15,
                )
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )

        return message_row  # Возвращаем строку сообщения
    
    def create_message_group(self, messages, user):
        is_my_message = user == self.username
        other_bg_color = "#E8F5E9" if self.theme_mode == ft.ThemeMode.LIGHT else "#2E3440"
        other_text_color = "#2E7D32" if self.theme_mode == ft.ThemeMode.LIGHT else "#88C0D0"
        
        # Контекстное меню
        menu_items = []
        if is_my_message:
            menu_items.append(
                ft.PopupMenuItem(
                    text=self.translate("Удалить"),
                    icon=ft.icons.DELETE,
                    on_click=lambda e, msg=messages[0]: self.delete_message(msg)
                )
            )
        menu_items.extend([
            ft.PopupMenuItem(
                text=self.translate("Ответить"),
                icon=ft.icons.REPLY,
                on_click=lambda e, msg=messages[0]: self.set_reply_to(msg)
            ),
            ft.PopupMenuItem(
                text=self.translate("Копировать"),
                icon=ft.icons.CONTENT_COPY,
                on_click=lambda e, msg=messages[0]: self.copy_message(msg)
            )
        ])
        
        header = ft.Row(
            [
                ft.Text(
                    f"{user}",
                    weight=ft.FontWeight.BOLD,
                    color=self.primary_color if is_my_message else ft.Colors.GREY_800,
                    size=14
                ),
                ft.Text(
                    messages[0]["created_at"].strftime("%H:%M"),
                    color=ft.Colors.GREY_600,
                    size=12
                )
            ], 
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.END if not is_my_message else ft.MainAxisAlignment.START
        )
        
        message_bubbles = ft.Column(
            [
                ft.Container(
                    content=ft.Text(
                        msg["text"],
                        color=other_text_color if not is_my_message else ft.Colors.WHITE,
                        size=16,
                        selectable=True
                    ),
                    bgcolor=self.primary_color if is_my_message else other_bg_color,
                    border=ft.border.all(1, "#C8E6C9" if self.theme_mode == ft.ThemeMode.LIGHT else "#434C5E"),
                    padding=ft.padding.symmetric(horizontal=15, vertical=10),
                    border_radius=15,
                    margin=ft.margin.only(bottom=3),
                    alignment=ft.alignment.center_right if not is_my_message else ft.alignment.center_left,
                ) for msg in messages
            ],
            spacing=3
        )
        
        return ft.Container(
            content=ft.Column([header, message_bubbles], spacing=5),
            margin=ft.margin.only(
                left=0 if is_my_message else 100,
                right=100 if is_my_message else 0
            ),
            alignment=ft.alignment.center_right if not is_my_message else ft.alignment.center_left,
            width=None,  # Убираем фиксированную ширину
        )

    def set_reply_to(self, message):
        self.reply_to_message = message
        self.show_reply_header()

    def show_reply_header(self):
        # Добавляем строку с информацией об ответе
        self.reply_header = ft.Row(
            [
                ft.Icon(ft.icons.REPLY, color=self.primary_color, size=20),
                ft.Text(
                    f"Отвечая на {self.reply_to_message['user']}: {self.reply_to_message['text'][:30]}...",
                    color=self.primary_color,
                    italic=True
                ),
                ft.IconButton(
                    icon=ft.icons.CLOSE,
                    icon_size=20,
                    on_click=self.clear_reply,
                    tooltip=self.translate("Отменить ответ")
                )
            ],
            visible=True
        )
        
        # Вставляем перед полем ввода
        if not hasattr(self, 'reply_header'):
            self.page.controls.insert(-1, ft.Container(
                content=self.reply_header,
                padding=ft.padding.only(left=15, top=5, bottom=5)
            ))
        self.page.update()

    def clear_reply(self, e):
        self.reply_to_message = None
        self.reply_header.visible = False
        self.page.update()

    def copy_message(self, message):
        self.page.set_clipboard(message["text"])
        self.page.show_snack_bar(
            ft.SnackBar(ft.Text(self.translate("Сообщение скопировано в буфер")), open=True)
        )

    def delete_message(self, message):
        try:
            headers = {"Authorization": f"Token {self.auth_token}"}
            response = requests.delete(
                f"http://127.0.0.1:8000/api/messages/{message['id']}/",
                headers=headers
            )
            if response.status_code == 204:
                self.messages = [m for m in self.messages if m.get('id') != message['id']]
                self.update_chat_display()
        except Exception as e:
            logging.error(f"Ошибка удаления: {e}")

    def logout(self, e):
        """Выход с полной перезагрузкой интерфейса"""
        self.page.clean()
        AuthApp(self.page)

class AuthApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.auth_token = page.client_storage.get("auth_token")
        self.login_attempts = 3
        self.last_failed_attempt = None
        self.language = "ru"
        self.theme_mode = ft.ThemeMode.DARK
        self.auto_login_attempted = False  # Добавляем флаг
        
        # Инициализируем элементы интерфейса ПЕРЕД загрузкой данных
        self.initialize_ui()  
        
        # Теперь загружаем данные, когда элементы уже созданы
        self.load_credentials()

    def load_credentials(self):
        """Загрузка и автоматический вход"""
        try:
            with open(CREDENTIALS_FILE, "r") as f:
                data = json.load(f)
                decrypted_user = uncipher(data['username'], mu=1)
                decrypted_pass = uncipher(data['password'], mu=1)
                
                if decrypted_user and decrypted_pass:
                    self.username_field.value = decrypted_user
                    self.password_field.value = decrypted_pass
                    self.page.update()
                    # Автоматический вход через 1 секунду
                    time.sleep(1)
                    self.login_click(None)
        except Exception as e:
            logging.info(f"Ошибка автоматического входа: {str(e)}")

    def save_credentials(self, username, password):
        """Сохранение учетных данных в файл"""
        try:
            data = {
                'username': cipher(username),
                'password': cipher(password)
            }
            with open(CREDENTIALS_FILE, "w") as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Error saving credentials: {str(e)}")

    def initialize_ui(self):
        """Инициализация интерфейса."""
        self.page.title = self.translate("Secure Auth")
        self.page.theme_mode = self.theme_mode
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.bgcolor = "#18181B"  # Используем цвет из CSS

        # Элементы управления
        self.username_field = ft.TextField(
            label=self.translate("Имя пользователя"),
            border_radius=15,
            prefix_icon=ft.Icons.PERSON,
            width=300,
            on_change=self.validate_fields,
            on_submit=lambda _: self.login_click(None)
        )

        self.password_field = ft.TextField(
            label=self.translate("Пароль"),
            password=True,
            can_reveal_password=True,
            border_radius=15,
            prefix_icon=ft.Icons.LOCK,
            width=300,
            on_change=self.validate_fields,
            on_submit=lambda _: self.login_click(None)
        )

        self.error_banner = ft.Container(
            bgcolor=ft.Colors.RED_700,
            padding=10,
            border_radius=10,
            visible=False,
            animate_opacity=300,
            content=ft.Text("", color=ft.Colors.WHITE)
        )

        self.loading_indicator = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=30, height=30, stroke_width=2),
                    ft.Text(self.translate("Проверяем данные..."), size=12)
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            visible=False,
            animate_opacity=300,
            alignment=ft.alignment.center
        )

        self.login_button = ft.ElevatedButton(
            text=self.translate("Войти"),
            icon=ft.Icons.LOGIN,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                padding=20,
                bgcolor=ft.Colors.BLUE_700,
                overlay_color=ft.Colors.BLUE_900
            ),
            width=200,
            animate_opacity=300,
            on_click=self.login_click
        )

        # Капча
        self.captcha_field = ft.TextField(
            label=self.translate("Введите капчу"),
            border_radius=15,
            width=300,
            visible=False
        )
        self.captcha_image = ft.Image(
            src="https://via.placeholder.com/150",
            width=150,
            height=50,
            visible=False
        )

        # Переключатель языка
        self.language_switcher = ft.Dropdown(
            options=[
                ft.dropdown.Option("ru", "Русский"),
                ft.dropdown.Option("en", "English")
            ],
            value=self.language,
            width=100,
            on_change=self.change_language
        )

        # Сборка интерфейса
        self.main_card = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(ft.Icons.SHIELD, size=50),
                        ft.Text(self.translate("Secure Login"), size=24),
                        self.username_field,
                        self.password_field,
                        self.captcha_image,
                        self.captcha_field,
                        self.error_banner,
                        ft.Stack(
                            [self.login_button, self.loading_indicator],
                            height=60
                        )
                    ],
                    spacing=25,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=ft.padding.symmetric(vertical=40, horizontal=30),
                width=400
            ),
            elevation=15,
            color=ft.Colors.with_opacity(0.65, "#27272A")  # Исправленный метод with_opacity
        )

        self.page.add(self.main_card)
    
    def auto_login(self):
        try:
            headers = {"Authorization": f"Token {self.auth_token}"}
            response = requests.get("http://127.0.0.1:8000/api/users/me/", headers=headers)
            if response.status_code == 200:
                user_data = response.json()
                self.page.clean()
                ChatInterface(
                    self.page,
                    user_data['username'],
                    self.theme_mode,
                    self.language,
                    self.auth_token
                )
                return True
        except Exception as e:
            logging.error(f"Auto-login error: {e}")
        return False

    def translate(self, text):
        """Локализация текста."""
        translations = {
            "ru": {
                "Secure Auth": "Безопасный вход",
                "Имя пользователя или Email": "Имя пользователя или Email",
                "Пароль": "Пароль",
                "Проверяем данные...": "Проверяем данные...",
                "Войти": "Войти",
                "Темная тема": "Темная тема",
                "Введите капчу": "Введите капчу",
                "Заполните все поля!": "Заполните все поля!",
                "Неверные учетные данные!": "Неверные учетные данные!",
                "Слишком много попыток!": "Слишком много попыток! Попробуйте позже.",
                "Успешный вход!": "Успешный вход!",
                "Выйти": "Выйти"
            },
            "en": {
                "Secure Auth": "Secure Auth",
                "Имя пользователя или Email": "Username or Email",
                "Пароль": "Password",
                "Проверяем данные...": "Checking data...",
                "Войти": "Login",
                "Темная тема": "Dark Theme",
                "Введите капчу": "Enter captcha",
                "Заполните все поля!": "Please fill all fields!",
                "Неверные учетные данные!": "Invalid credentials!",
                "Слишком много попыток!": "Too many attempts! Try again later.",
                "Успешный вход!": "Login successful!",
                "Выйти": "Logout"
            }
        }
        return translations[self.language].get(text, text)

    def change_language(self, e):
        """Смена языка интерфейса."""
        self.language = self.language_switcher.value
        self.reset_ui()

    def reset_ui(self):
        """Сброс интерфейса."""
        self.page.clean()
        self.initialize_ui()

    def validate_fields(self, e):
        """Автовход при заполнении полей"""
        if os.path.exists(CREDENTIALS_FILE):
            if len(self.username_field.value) > 3 and len(self.password_field.value) > 5:
                self.login_click(None)
        """Валидация полей ввода."""
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        is_email_valid = re.match(email_regex, self.username_field.value) if "@" in self.username_field.value else True
        is_password_valid = len(self.password_field.value) >= 6

        self.username_field.error_text = (
            self.translate("Неверный формат email") if "@" in self.username_field.value and not is_email_valid else ""
        )
        self.password_field.error_text = (
            self.translate("Пароль должен быть не менее 6 символов") if not is_password_valid else ""
        )
        self.page.update()

    def login_click(self, e):
        """Обработчик входа (с автоматическим вызовом)"""
        if self.auto_login_attempted:  # Защита от повторных попыток
            return
        self.auto_login_attempted = True
        """Обработчик нажатия на кнопку входа."""
        if self.block_login():
            return

        username = self.username_field.value.strip()
        password = self.password_field.value.strip()

        self.error_banner.visible = False
        self.page.update()

        if not username or not password:
            self.error_banner.content.value = self.translate("Заполните все поля!")
            self.error_banner.visible = True
            self.page.update()
            return

        self.toggle_ui_elements(True)
        time.sleep(1)  # Имитация задержки сети

        if self.validate_credentials(username, password):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/api-token-auth/",
                    data={"username": username, "password": password}
                )
                if response.status_code == 200:
                    self.auto_login_attempted = False
                    auth_token = response.json()['token']
                    self.page.client_storage.set("auth_token", auth_token)
                    self.page.client_storage.set("username", username)
                    self.save_credentials(username, password)  # Перенесено сюда
                    self.page.clean()
                    ChatInterface(
                        self.page, 
                        username, 
                        self.theme_mode,
                        self.language,
                        auth_token
                    )
                    logging.info(f"Успешный вход: {username}")
            except Exception as e:
                logging.error(f"Ошибка получения токена: {str(e)}")
        else:
            self.login_attempts -= 1  # Уменьшаем количество оставшихся попыток вместо увеличения
            self.last_failed_attempt = time.time()
            self.toggle_ui_elements(False)
            self.error_banner.content.value = self.translate("Неверные учетные данные!")
            self.error_banner.visible = True
            self.show_captcha()
            logging.warning(f"Failed login attempt: {username}")
            self.page.update()

    @staticmethod
    def translate_static(lang, text):
        """Статический метод для локализации"""
        translations = {
            "ru": {
                "Global Chat": "Глобальный чат",
                "Новое сообщение": "Новое сообщение",
                "Выйти": "Выйти",
                "Secure Auth": "Безопасный вход",
                "Имя пользователя или Email": "Имя пользователя или Email",
                "Пароль": "Пароль",
                "Проверяем данные...": "Проверяем данные...",
                "Войти": "Войти",
                "Темная тема": "Темная тема",
                "Введите капчу": "Введите капчу",
                "Заполните все поля!": "Заполните все поля!",
                "Неверные учетные данные!": "Неверные учетные данные!",
                "Слишком много попыток!": "Слишком много попыток! Попробуйте позже.",
                "Успешный вход!": "Успешный вход!",
            },
            "en": {
                "Global Chat": "Global Chat",
                "Новое сообщение": "New message",
                "Выйти": "Logout",
                "Secure Auth": "Secure Auth",
                "Имя пользователя или Email": "Username or Email",
                "Пароль": "Password",
                "Проверяем данные...": "Checking data...",
                "Войти": "Login",
                "Темная тема": "Dark Theme",
                "Введите капчу": "Enter captcha",
                "Заполните все поля!": "Please fill all fields!",
                "Неверные учетные данные!": "Invalid credentials!",
                "Слишком много попыток!": "Too many attempts! Try again later.",
                "Успешный вход!": "Login successful!",
            }
        }
        return translations[lang].get(text, text)

    def validate_credentials(self, username, password):
        """Проверка учетных данных."""
        users = self.get_users()
        for user in users:
            if (user['username'] == username or user['email'] == username):
                try:
                    return django_pbkdf2_sha256.verify(password, user['password'])
                except Exception as e:
                    logging.error(f"Password check error: {e}")
                    return False
        return False

    def get_users(self):
        """Получение пользователей из API."""
        try:
            response = requests.get("http://127.0.0.1:8000/api/users/")
            if response.status_code == 200:
                users_data = json.loads(response.json()['users'])
                return [
                    {
                        'username': user['fields']['username'],
                        'email': user['fields']['email'],
                        'password': user['fields']['password']
                    }
                    for user in users_data
                ]
            return []
        except Exception as e:
            logging.error(f"API Error: {e}")
            return []

    def toggle_ui_elements(self, loading: bool):
        """Переключение состояния UI."""
        self.login_button.disabled = loading
        self.login_button.opacity = 0 if loading else 1
        self.loading_indicator.visible = loading
        self.loading_indicator.opacity = 1 if loading else 0
        self.page.update()

    def show_captcha(self):
        """Показ капчи после нескольких неудачных попыток."""
        if self.login_attempts >= MAX_LOGIN_ATTEMPTS:
            self.captcha_image.visible = True
            self.captcha_field.visible = True
            self.page.update()

    def block_login(self):
        """Блокировка входа на определенное время."""
        if self.last_failed_attempt and (time.time() - self.last_failed_attempt) < BLOCK_TIME:
            self.error_banner.content.value = self.translate("Слишком много попыток!")
            self.error_banner.visible = True
            self.page.update()
            return True
        return False

def main(page: ft.Page):
    AuthApp(page)

if __name__ == "__main__":
    ft.app(target=main)