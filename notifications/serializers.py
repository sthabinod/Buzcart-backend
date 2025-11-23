
from rest_framework import serializers
from .models import DeviceToken
class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ['id','user_id','token','platform','created_at']
        read_only_fields = ['id','created_at']
