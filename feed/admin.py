from django.contrib import admin
from .models import Post, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'type', 'caption', 'post_media', 'product_linked', 'likes', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('caption', 'user__username')
    
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'user', 'text', 'created_at')
    list_filter = ('post', 'created_at')
    search_fields = ('text', 'user__username')
    
