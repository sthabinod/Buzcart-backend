from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer, LikeResponseSerializer, CommentCreateRequestSerializer

# Swagger helpers
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiResponse, OpenApiParameter, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.permissions import IsAuthenticated

class PostListCreate(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return super().get_permissions()
    
    @extend_schema(
        summary="List all posts",
        description="Retrieve all posts with captions, media, and like counts.",
        responses={200: PostSerializer(many=True)}
    )
    def get(self, request):
        qs = Post.objects.all()
        return Response(PostSerializer(qs, many=True).data)

    @extend_schema(
        summary="Create a new post",
        request=PostSerializer,
        responses={
            201: PostSerializer,
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Feed - Posts"]
    )
    def post(self, request):
        ser = PostSerializer(data=request.data, context={"request": request})
        if ser.is_valid():
            post = ser.save()
            return Response(PostSerializer(post).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Feed - Posts"])
class PostDetail(APIView):
    @extend_schema(
        summary="Retrieve a post by ID",
        responses={200: PostSerializer, 404: OpenApiResponse(description="Not found")}
    )
    def get(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        return Response(PostSerializer(post).data)

    @extend_schema(
        summary="Update post (partial)",
        request=PostSerializer,
        responses={200: PostSerializer, 400: OpenApiResponse(description="Validation error")}
    )
    def put(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        ser = PostSerializer(post, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete post",
        responses={204: OpenApiResponse(description="Deleted"), 404: OpenApiResponse(description="Not found")}
    )
    def delete(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Feed - Likes"])
class PostLike(APIView):
    @extend_schema(
        summary="Like a post",
        description="Increment the like count for the given post.",
        responses={200: LikeResponseSerializer, 404: OpenApiResponse(description="Not found")}
    )
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        post.likes += 1
        post.save()
        return Response({'id': str(post.id), 'likes': post.likes})


@extend_schema(tags=["Feed - Comments"])
class CommentCreate(APIView):
    @extend_schema(
        summary="Add a comment to a post",
        request=CommentCreateRequestSerializer,
        responses={201: CommentSerializer, 400: OpenApiResponse(description="Validation error")}
    )
    def post(self, request, **kwargs):
        payload = dict(request.data)
        post_id = kwargs.get("post_id")
        post = get_object_or_404(Post, pk=post_id)
        ser = CommentSerializer(data=payload, context={"request": request, "post": post})
        if ser.is_valid():
            c = ser.save()
            return Response(CommentSerializer(c).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
