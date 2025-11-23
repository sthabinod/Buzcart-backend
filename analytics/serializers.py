
from rest_framework import serializers
from .models import UserActivity
class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id','user_id','activity_type','timestamp','payload']
        read_only_fields = ['id','timestamp']
