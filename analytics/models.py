
from django.db import models
import uuid
class UserActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(help_text="ID of the user performing the activity")
    activity_type = models.CharField(max_length=255, help_text="e.g., 'post_view', 'like', 'purchase'")
    timestamp = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict, blank=True, help_text="Additional data")
    class Meta:
        ordering = ['-timestamp']
