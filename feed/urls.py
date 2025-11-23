
from django.urls import path
from .views import PostListCreate, PostDetail, PostLike, CommentCreate
urlpatterns = [
    path('posts/', PostListCreate.as_view()),
    path('posts/<uuid:pk>/', PostDetail.as_view()),
    path('posts/<uuid:pk>/like/', PostLike.as_view()),
    path('posts/<uuid:post_id>/comments/', CommentCreate.as_view()),
]
