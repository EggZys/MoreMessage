from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.serializers import serialize
from .forms import RegistrationForm
from .models import CustomUser, Server
import os
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import logout, login
from rest_framework import generics
from .models import ChatMessage
from .serializers import ChatMessageSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status


def home_view(request):
    user = request.user
    users = len(CustomUser.objects.all())
    messages = len(ChatMessage.objects.all())
    return render(request, 'home.html', context={'user': user, 'messages': messages, 'users': users})

def profile_view(request):
    user = request.user
    msgs = ChatMessage.objects.filter(user=request.user).count()
    return render(request, 'profile.html', {'user': user, 'msgs': msgs})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            login(request, user)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def download_view(request):
    return render(request, 'download.html')

def download_file(request):
    # Формируем полный путь к файлу
    file_path = os.path.join(settings.MEDIA_ROOT, 'prog', 'aga.txt')
    
    # Печатаем путь в консоль (или лог)
    print(f"Путь к файлу: {file_path}")
    
    # Если файл не найден, возвращаем сообщение с путём
    if not os.path.exists(file_path):
        return HttpResponse(f"Файл не найден. Путь: {file_path}", status=404)
    
    # Если найден, возвращаем файл
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="aga.txt"'
        return response


def api_users_view(request):
    users = CustomUser.objects.all()
    data = serialize('json', users, fields=('username', 'email', 'password'))
    return JsonResponse({'users': data})

def unauthorized_view(request):
    return render(request, 'unauthorized.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def coming_view(request):
    return render(request, 'coming.html')

class ChatMessageListCreate(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]  # Добавить эту строку
    queryset = ChatMessage.objects.all().order_by('-created_at')[:100]
    serializer_class = ChatMessageSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserDetailView(APIView):
    def get(self, request, username):
        try:
            user = CustomUser.objects.get(username=username)
            return Response({
                "username": user.username,
                "email": user.email
            })
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

def about(request):
    users = len(CustomUser.objects.all())
    return render(request, 'about.html', {'users': users})

def career(request):
    return render(request, 'career.html')

def support(request):
    return render(request, 'support.html')

def status(request):
    servers = Server.objects.all()
    status_data = {
        "overall": "outage",
        "overall_status": "Не в сети.",
        "services": [
            {
                "icon": "fa-server",
                "name": "Сервер сообщений",
                "status": "outage",
                "status_text": "Выключен..."
            },
            {
                "icon": "fa-database",
                "name": "База данных",
                "status": "outage",
                "status_text": "Выключена..."
            },
            {
                "icon": "fa-cloud",
                "name": "Облачное хранилище",
                "status": "outage",
                "status_text": "Выключено..."
            }
        ]
    }
    return render(request, 'status.html', {'status': status_data, 'servers': servers})

def contact(request):
    return render(request, 'contact.html')