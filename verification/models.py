
from django.db import models
from django.contrib.auth.models import User
import uuid

DOCUMENT_CHOICE = (
    ('passport', 'Passport'),
    ('national_id', 'National ID'),
    ('driver_license', 'Driver License'),
    ('other', 'Other'),
)
DOCUMENT_VERIFICATION_STATUS = (
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
)
class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='documents')
    doc_type = models.CharField(max_length=50, choices=DOCUMENT_CHOICE)
    doc_file = models.FileField(upload_to='documents/verification/')
    status = models.CharField(max_length=20, choices=DOCUMENT_VERIFICATION_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, default='')
    class Meta:
        ordering = ['-created_at']
