from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.core.serializers import serialize
from .forms import RegistrationForm
from .models import CustomUser


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
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def download_view(request):
    return render(request, 'download.html')

def api_users_view(request):
    users = CustomUser.objects.all()
    data = serialize('json', users, fields=('username', 'email', 'password'))
    return JsonResponse({'users': data})

def unauthorized_view(request):
    return render(request, 'unauthorized.html')