
from django.db import models
from django.contrib.auth.models import User

import uuid
class Post(models.Model):
    class PostType(models.TextChoices):
        CLIP = "clip", "Clip"
        IMAGE = "image", "Image"
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    type = models.CharField(max_length=10, default='clip', choices=PostType.choices)
    caption = models.TextField(blank=True)
    post_media = models.FileField(upload_to='post_media/')
    product_id = models.UUIDField(null=True, blank=True)  # reference to commerce.Product
    likes = models.PositiveIntegerField(default=0)
    link_product = models.BooleanField(default=False)
    product_linked = models.OneToOneField('commerce.Product', on_delete=models.CASCADE, null=True, blank=True, related_name='post_linked')
    created_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

