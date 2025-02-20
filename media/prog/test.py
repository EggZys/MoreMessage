import sys
import random
from datetime import datetime
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

class AvatarWidget(QWidget):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setFixedSize(40, 40)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  # Игнорируем события мыши
        self.color = self.generate_color(user)
        
    def generate_color(self, seed):
        random.seed(hash(seed))
        colors = [
            QColor("#FF6B6B"), QColor("#4ECDC4"), QColor("#45B7D1"),
            QColor("#96CEB4"), QColor("#FFEEAD"), QColor("#D4A5A5")
        ]
        return random.choice(colors)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Рисуем круглый фон
        path = QPainterPath()
        path.addEllipse(0, 0, 40, 40)
        painter.setClipPath(path)
        
        # Заливаем цветом
        painter.setBrush(self.color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 40, 40)
        
        # Рисуем инициалы
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.setPen(QColor("white"))
        initials = ''.join([name[0] for name in self.user.split()[:2]]).upper()
        painter.drawText(QRect(0, 0, 40, 40), Qt.AlignmentFlag.AlignCenter, initials)

class MessageWidget(QWidget):
    def __init__(self, user, text, is_me=False):
        super().__init__()
        self.is_me = is_me
        self.setup_ui(user, text)
        self.setup_effects()

    def setup_ui(self, user, text):
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(10, 5, 10, 5)
        self.layout.setSpacing(10)

        # Контент сообщения
        content = QVBoxLayout()
        header = QHBoxLayout()
        
        self.username = QLabel(user)
        self.username.setStyleSheet("font-weight: bold; color: #2ecc71;")
        self.time = QLabel(datetime.now().strftime("%H:%M"))
        self.time.setStyleSheet("color: #95a5a6; font-size: 10px;")
        
        header.addWidget(self.username)
        header.addWidget(self.time)
        header.addStretch()
        
        self.message = QLabel(text)
        self.message.setStyleSheet("""
            background: #34495e;
            color: white;
            padding: 10px;
            border-radius: 12px;
            margin: 2px;
        """)
        self.message.setWordWrap(True)
        self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        content.addLayout(header)
        content.addWidget(self.message)
        
        # Аватарка
        self.avatar = AvatarWidget(user)
        
        if self.is_me:
            self.layout.addStretch()
            self.layout.addLayout(content)
            self.layout.addWidget(self.avatar)
            self.message.setStyleSheet("""
                background: #2ecc71;
                color: white;
                padding: 10px;
                border-radius: 12px;
                margin: 2px;
            """)
        else:
            self.layout.addWidget(self.avatar)
            self.layout.addLayout(content)
            self.layout.addStretch()

        self.setLayout(self.layout)

    def setup_effects(self):
        # Эффект тени
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(3, 3)
        self.message.setGraphicsEffect(shadow)

        # Анимация появления
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_styles()
        self.users = ["John Doe", "Alice Smith", "Bob Johnson"]
        self.current_user = "Me"

    def setup_ui(self):
        self.setWindowTitle("Global Chat")
        self.setGeometry(100, 100, 800, 600)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        
        # Список сообщений
        self.chat_list = QListWidget()
        self.chat_list.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.chat_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.chat_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                border-radius: 10px;
            }
            QScrollBar:vertical {
                width: 8px;
                background: rgba(52, 73, 94, 150);
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #7f8c8d;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.chat_list)

        # Панель ввода
        input_panel = QHBoxLayout()
        
        self.input = QTextEdit()
        self.input.setPlaceholderText("Type your message...")
        self.input.setMaximumHeight(45)
        self.input.setStyleSheet("""
            QTextEdit {
                background: rgba(52, 73, 94, 200);
                color: white;
                border: 2px solid #2ecc71;
                border-radius: 15px;
                padding: 5px;
                font-size: 14px;
            }
        """)
        self.input.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setFixedSize(100, 40)
        self.send_btn.clicked.connect(self.send_message)
        self.input.returnPressed = self.send_message
        
        input_panel.addWidget(self.input)
        input_panel.addWidget(self.send_btn)
        layout.addLayout(input_panel)
    

    def setup_styles(self):
        # Градиентный фон
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#2c3e50"))
        gradient.setColorAt(1, QColor("#3498db"))
        
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366F1, stop:1 #EC4899);
            }}
            QListWidget {{
                background: rgba(39, 39, 42, 0.65);
                border-radius: 15px;
                padding: 10px;
            }}
            QScrollBar:vertical {{
                background: rgba(255,255,255,0.1);
                width: 8px;
                border-radius: 4px;
            }}
        """)
    
    def setup_effects(self, animate=True):
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(3, 3)
        self.message.setGraphicsEffect(shadow)

        if animate:
            self.animation = QPropertyAnimation(self, b"windowOpacity")
            self.animation.setDuration(500)
            self.animation.setStartValue(0)
            self.animation.setEndValue(1)
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animation.start()

    def send_message(self):
        text = self.input.toPlainText().strip()
        if text:
            self.add_message(self.current_user, text, is_me=True)
            self.input.clear()
            
            # Имитация ответа
            QTimer.singleShot(1000, lambda: self.add_message(
                random.choice(self.users), 
                random.choice(["Cool!", "Nice!", "Interesting!", "Thanks!"])
            ))

    def add_message(self, user, text, is_me=False):
        item = QListWidgetItem()
        widget = MessageWidget(user, text, is_me)
        item.setSizeHint(widget.sizeHint())
        
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, widget)
        
        # Плавная прокрутка до последнего сообщения
        final_pos = self.chat_list.verticalScrollBar().maximum()
        self._animate_scroll(final_pos)
    
    def _animate_scroll(self, final_pos):
        self.animation = QPropertyAnimation(self.chat_list.verticalScrollBar(), b"value")
        self.animation.setDuration(500)
        self.animation.setStartValue(self.chat_list.verticalScrollBar().value())
        self.animation.setEndValue(final_pos)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())