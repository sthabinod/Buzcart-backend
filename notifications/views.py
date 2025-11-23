
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import DeviceTokenSerializer
class DeviceTokenView(APIView):
    def post(self, request):
        ser = DeviceTokenSerializer(data=request.data)
        if ser.is_valid():
            obj = ser.save()
            return Response(DeviceTokenSerializer(obj).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
