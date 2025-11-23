from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from .models import Document
from .serializers import DocumentSerializer

# drf-spectacular imports
from drf_spectacular.utils import (
    extend_schema, OpenApiParameter, OpenApiResponse
)
from drf_spectacular.types import OpenApiTypes


@extend_schema(tags=["Verification - Documents"])
class DocumentListCreate(APIView):
    @extend_schema(
        summary="List submitted verification documents",
        responses={200: DocumentSerializer(many=True)}
    )
    def get(self, request):
        qs = Document.objects.all()
        return Response(DocumentSerializer(qs, many=True).data)

    @extend_schema(
        summary="Submit a verification document",
        request=DocumentSerializer,
        responses={201: DocumentSerializer, 400: OpenApiResponse(description="Validation error")}
    )
    def post(self, request):
        ser = DocumentSerializer(data=request.data, context={"request": request})
        if ser.is_valid():
            doc = ser.save()  # status defaults to 'pending'
            return Response(DocumentSerializer(doc).data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
