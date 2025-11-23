from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_id', 'doc_type', 'doc_file', 'status', 'created_at', 'reviewed_at')
    list_filter = ('created_at', )
    search_fields = ('user_id', 'doc_type', 'doc_file', 'status')
