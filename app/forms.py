from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm


class RegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            "username": "Имя пользователя",
            "email": "Электронная почта",
            "password1": "Пароль",
            "password2": "Подтверждение пароля",
        }