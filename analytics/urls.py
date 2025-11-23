from django.urls import path
from .views import ActivityView
urlpatterns=[path('activity/', ActivityView.as_view())]
