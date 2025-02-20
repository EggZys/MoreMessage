from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ChatMessage, Server, Stat

# Создание кастомного интерфейса для CustomUser
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'is_staff', 'is_active')  # Поля для отображения
    list_filter = ('is_staff', 'is_active')  # Фильтры
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}),
    )
    search_fields = ('username', 'email')  # Поля для поиска
    ordering = ('username',)

# Регистрируем модель CustomUser с кастомным интерфейсом
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(ChatMessage)
admin.site.register(Server)
admin.site.register(Stat)