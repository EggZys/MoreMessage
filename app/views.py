from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from .forms import RegistrationForm
from .models import CustomUser
from django.http import FileResponse
import os
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import logout, login


def home_view(request):
    user = request.user
    return render(request, 'home.html', context={'user': user})

def profile_view(request):
    user = request.user
    return render(request, 'profile.html', {'user': user})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            login(request, form.instance)
            return redirect('home')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def download_view(request):
    return render(request, 'download.html')

def download_file(request):
    # Формируем полный путь к файлу
    file_path = os.path.join(settings.MEDIA_ROOT, 'prog', 'MoreMessage.exe')
    
    # Печатаем путь в консоль (или лог)
    print(f"Путь к файлу: {file_path}")
    
    # Если файл не найден, возвращаем сообщение с путём
    if not os.path.exists(file_path):
        return HttpResponse(f"Файл не найден. Путь: {file_path}", status=404)
    
    # Если найден, возвращаем файл
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="MoreMessage.exe"'
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