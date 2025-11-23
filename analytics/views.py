
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserActivitySerializer
from .models import UserActivity
class ActivityView(APIView):
    def get(self, request):
        qs = UserActivity.objects.all()[:50]
        return Response(UserActivitySerializer(qs, many=True).data)
    def post(self, request):
        ser = UserActivitySerializer(data=request.data)
        if ser.is_valid():
            obj = ser.save()
            return Response(UserActivitySerializer(obj).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
