
from django.urls import path
from .views import MeView, RegisterView, ProfileMePatchView, ChangePasswordView
urlpatterns = [
    path('me/', MeView.as_view()),
    path("profile-update/", ProfileMePatchView.as_view()),
    path("change-password/", ChangePasswordView.as_view(), name="me-change-password"),
    path('register/', RegisterView.as_view()),
]
