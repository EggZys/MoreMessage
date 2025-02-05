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
    download_file,
    logout_view,
    ChatMessageListCreate,
    UserDetailView,
    coming_view,
)
from rest_framework.authtoken.views import obtain_auth_token


urlpatterns = [
    path('', home_view, name='home'),
    path('profile/', profile_view, name='profile'),
    path('register/', register_view, name='register'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', logout_view, name='logout'),
    path('api/users/', api_users_view, name='api_users'),
    path('api/messages/', ChatMessageListCreate.as_view(), name='message-list'),
    path('unauthorized/', unauthorized_view, name='unauthorized'),
    path('download/', download_view, name='download'),
    path('download/windows/', download_file, name='download_windows'),
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),
    path("api/users/<str:username>/", UserDetailView.as_view(), name="user-detail"),
    path('coming/', coming_view, name='coming')
]
