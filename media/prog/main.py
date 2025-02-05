import flet as ft
import requests
import json
import re
import time
import logging
from passlib.hash import django_pbkdf2_sha256
from datetime import datetime
import socket
import asyncio
import websockets

hostname = socket.gethostname()
ip_address = socket.gethostbyname(hostname)

# Настройка логирования
logging.basicConfig(
    filename="auth.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Конфигурация
MAX_LOGIN_ATTEMPTS = 3  # Максимальное количество попыток входа
BLOCK_TIME = 60  # Время блокировки в секундах после превышения попыток

class ChatInterface:
    def __init__(self, page, username, theme_mode, language, auth_token):
        self.page = page
        self.username = username
        self.theme_mode = theme_mode
        self.language = language
        self.auth_token = auth_token
        self.messages = []
        self.ws = None  # WebSocket клиент
        self.initialize_ui()
        asyncio.create_task(self.connect_websocket())  # 🚀 Запускаем WebSocket
    
    async def connect_websocket(self):
        """🔌 Подключаемся к WebSocket"""
        try:
            self.ws = await websockets.connect("ws://127.0.0.1:8000/ws/chat/")
            print("✅ Подключено к WebSocket!")

            while True:
                message = await self.ws.recv()
                data = json.loads(message)
                print(f"📥 [WebSocket] Получено сообщение: {data}")  # 👀 Проверяем, приходят ли чужие сообщения

                self.messages.append(data)
                self.update_chat_display()  # 🔄 Обновляем чат
        except Exception as e:
            print(f"❌ [WebSocket] Ошибка: {e}")

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
        return {
            "username": self.username,
            "email": "неизвестно@example.com",
            "avatar": "👤"
        }

    def initialize_ui(self):
        """Инициализация красивого интерфейса чата"""
        self.page.clean()
        self.page.title = self.translate("Global Chat")
        self.page.theme_mode = self.theme_mode
        self.page.padding = 20
        
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
        self.new_message = ft.TextField(
            label=self.translate("Напишите сообщение..."),
            multiline=True,
            min_lines=1,
            max_lines=5,
            border_radius=20,
            filled=True,
            expand=True,
            on_submit=self.send_message,
            border_color=self.primary_color
        )
        
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND_ROUNDED,
            icon_size=32,
            icon_color=self.primary_color,
            tooltip=self.translate("Отправить"),
            on_click=self.send_message
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
            ft.Row(
                [self.new_message, self.send_button],
                spacing=15,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.END
            )
        )
        
        self.load_messages()
        self.page.update()

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
        """✉️ Отправка сообщения через WebSocket"""
        message = self.new_message.value.strip()
        if not message:
            return

        timestamp = datetime.now().strftime("%H:%M:%S")

        data = {"user": self.username, "text": message}

        # 🔥 Локально добавляем в UI, чтобы сообщение сразу появилось
        self.messages.append({
            "user": self.username,
            "text": message,
            "time": timestamp
        })
        self.update_chat_display()

        # 📡 Отправляем через WebSocket
        if self.ws:
            asyncio.create_task(self.ws.send(json.dumps(data)))

        # 🧹 Очищаем поле ввода
        self.new_message.value = ""
        self.page.update()

    def load_messages(self):
        """Загрузка сообщений с сервера"""
        try:
            headers = {
                "Authorization": f"Token {self.auth_token}",
                "Content-Type": "application/json"
            }
            response = requests.get("http://127.0.0.1:8000/api/messages/", headers=headers)
            if response.status_code == 200:
                messages_data = response.json()
                logging.info(f"Данные от сервера: {messages_data}")
                self.messages = []
                for msg in messages_data:
                    # Получаем имя пользователя через отдельный запрос
                    user_response = requests.get(
                        f"http://127.0.0.1:8000/api/users/{msg['user']}/",
                        headers=headers
                    )
                    if user_response.status_code == 200:
                        user_data = user_response.json()
                        username = user_data.get('username', 'unknown')
                    else:
                        username = 'unknown'
                    
                    self.messages.append({
                        "user": username,  # Используем полученное имя
                        "text": msg['text'],
                        "time": datetime.strptime(msg['created_at'], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%H:%M:%S")
                    })
                self.update_chat_display()
        except Exception as e:
            logging.error(f"Ошибка загрузки сообщений: {str(e)}")

    def update_chat_display(self):
        """Обновление отображения сообщений"""
        self.chat_messages.controls = [
            ft.ListTile(
                title=ft.Text(f"{msg['user']} ({msg['time']})"),
                subtitle=ft.Text(msg['text']),
            ) for msg in self.messages
        ]
        self.page.update()
    
    def create_message_bubble(self, message: dict):
        is_my_message = message["user"] == self.username
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    f"{message['user']} • {message['time']}",
                    size=12,
                    color=ft.Colors.GREY_500
                ),
                ft.Text(
                    message["text"], 
                    size=16,
                    color=self.text_color,
                    width=300,  # Фиксированная ширина
                    max_lines=10,
                    overflow=ft.TextOverflow.ELLIPSIS
                )
            ], spacing=5),
            bgcolor=self.primary_color if is_my_message else ft.Colors.ON_SURFACE_VARIANT,
            padding=15,
            border_radius=15,
            alignment=ft.alignment.center_left,
            margin=ft.margin.only(
                left=100 if not is_my_message else 0,
                right=0 if not is_my_message else 100
            ),
            width=300  # Ширина контейнера
        )


    def update_chat_display(self):
        """Обновление отображения с красивыми сообщениями"""
        self.chat_messages.controls = [
            self.create_message_bubble(msg) for msg in self.messages
        ]
        self.page.update()

    def logout(self, e):
        """Выход с полной перезагрузкой интерфейса"""
        self.page.clean()
        AuthApp(self.page)

class AuthApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.login_attempts = 3
        self.last_failed_attempt = None
        self.language = "ru"  # По умолчанию русский язык
        self.theme_mode = ft.ThemeMode.DARK  # По умолчанию темная тема
        self.initialize_ui()

    def initialize_ui(self):
        """Инициализация интерфейса."""
        self.page.title = self.translate("Secure Auth")
        self.page.theme_mode = self.theme_mode
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.bgcolor = ft.Colors.BLUE_GREY_900 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_100

        # Элементы управления
        self.username_field = ft.TextField(
            label=self.translate("Имя пользователя или Email"),
            border_radius=15,
            prefix_icon=ft.Icons.PERSON,
            width=300,
            on_change=self.validate_fields
        )

        self.password_field = ft.TextField(
            label=self.translate("Пароль"),
            password=True,
            can_reveal_password=True,
            border_radius=15,
            prefix_icon=ft.Icons.LOCK,
            width=300,
            on_change=self.validate_fields
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

        # Элементы управления
        self.username_field = ft.TextField(
            label=self.translate("Имя пользователя или Email"),
            border_radius=15,
            prefix_icon=ft.Icons.PERSON,
            width=300,
            on_change=self.validate_fields
        )

        self.password_field = ft.TextField(
            label=self.translate("Пароль"),
            password=True,
            can_reveal_password=True,
            border_radius=15,
            prefix_icon=ft.Icons.LOCK,
            width=300,
            on_change=self.validate_fields
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
            color=ft.Colors.BLUE_GREY_800 if self.theme_mode == ft.ThemeMode.DARK else ft.Colors.WHITE
        )

        self.page.add(self.main_card)

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
            # Получаем токен после успешного входа
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/api-token-auth/",
                    data={"username": username, "password": password}
                )
                if response.status_code == 200:
                    auth_token = response.json()['token']
                    self.page.client_storage.set("auth_token", auth_token)
                    self.page.clean()
                    ChatInterface(
                        self.page, 
                        username, 
                        self.theme_mode,
                        self.language,
                        auth_token  # Явно передаем токен
                    )
                    logging.info(f"Успешный вход: {username}")
            except Exception as e:
                logging.error(f"Ошибка получения токена: {str(e)}")
        else:
            self.login_attempts += 1
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
    print(f"Hostname: {hostname}")
    print(f"IP Address: {ip_address}")