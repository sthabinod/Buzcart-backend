from django.urls import path
from .views import DeviceTokenView
urlpatterns=[path('device/', DeviceTokenView.as_view())]
