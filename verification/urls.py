from django.urls import path
from .views import DocumentListCreate

urlpatterns=[
    path(
        'documents/',
         DocumentListCreate.as_view()
         ),
]