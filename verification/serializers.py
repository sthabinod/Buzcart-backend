
from rest_framework import serializers
from .models import Document
class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id','doc_type','doc_file','status','created_at','reviewed_at','note']
        read_only_fields = ['id','status','created_at','reviewed_at','note']
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        return Document.objects.create(**validated_data)

class DocumentApproveRequestSerializer(serializers.Serializer):
    note = serializers.CharField(required=False, allow_blank=True, default="")