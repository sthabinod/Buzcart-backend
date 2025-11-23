
from django.db import models
import uuid
class DeviceToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(null=True, blank=True)
    token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(max_length=20, default='web')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
