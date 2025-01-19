from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from .views import (
    home_view,
    profile_view,
    register_view,
    api_users_view,
    unauthorized_view,
    download_view,
)

urlpatterns = [
    path('', home_view, name='home'),
    path('profile/', profile_view, name='profile'),
    path('register/', register_view, name='register'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page=reverse_lazy('login')), name='logout'),
    path('api/users/', api_users_view, name='api_users'),
    path('unauthorized/', unauthorized_view, name='unauthorized'),
    path('download/', download_view, name='download'),
]
