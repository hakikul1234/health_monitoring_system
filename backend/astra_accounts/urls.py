from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    DemoSessionView,
    RefreshTokenView,
    CurrentUserView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("demo-session/", DemoSessionView.as_view(), name="demo_session"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
]
