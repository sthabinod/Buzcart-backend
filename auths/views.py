from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_spectacular.utils import extend_schema
from .serializers import RegisterSerializer, CustomTokenObtainPairSerializer, ChangePasswordSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import (
    extend_schema, OpenApiResponse, OpenApiExample
)
from verification.models import Document
from verification.serializers import DocumentSerializer

from .serializers import MeSerializer, ProfileSerializer, MeUpdateSerializer
from .models import Profile
from commerce.models import Order
from .utils import get_total_spent



@extend_schema(
    tags=["Authentication"],
    summary="Register a new user",
    description=(
        "Registers a new user with a username and password. "
        "Returns the created user details upon success."
    ),
    request=RegisterSerializer,
    responses={
        201: {
            "type": "object",
            "properties": {
                "id": {"type": "integer", "example": 12},
                "username": {"type": "string", "example": "new_user"},
            },
        },
        400: {"description": "Invalid input or missing fields"},
    },
)
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if ser.is_valid():
            user = ser.save()
            return Response(
                {"id": user.id, "username": user.username},
                status=status.HTTP_201_CREATED,
            )
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    



def _find_user_fk(model):
    """
    Try common FK names pointing to the auth user.
    Returns the field name string.
    """
    candidates = ["user", "customer", "owner", "created_by", "buyer"]
    for name in candidates:
        try:
            field = model._meta.get_field(name)
            # accept FK or OneToOne to user model
            if hasattr(field, "remote_field") and field.remote_field:
                return name
        except FieldDoesNotExist:
            continue
    # last resort: raise a loud error so we don't silently return zeroes
    raise RuntimeError("Order model: could not locate a FK to the user (tried user/customer/owner/created_by/buyer).")

def _compute_stats(user):
    """
    Build the numbers for the dashboard tiles:
      - orders_count       : all orders placed by the user
      - pending_orders_count: pending/processing orders
      - total_spent        : sum of 'total' for successful orders (exclude canceled/refunded/failed)
      - currency           : static label (adjust if you add multi-currency later)
      - last_order_at      : latest created_at
    """
    currency = "NPR"  # change if needed

    # --- Figure out the user field on Order
    user_fk = _find_user_fk(Order)

    # --- Base queryset
    orders_qs = Order.objects.filter(**{user_fk: user})

    # --- Counts
    orders_count = orders_qs.count()

    # Adjust these to your actual statuses
    PENDING_STATUSES = {"pending", "processing"}
    SUCCESS_STATUSES = {"paid", "completed", "delivered", "shipped"}  # treated as "spent"
    EXCLUDE_FROM_SPEND = {"canceled", "cancelled", "refunded", "failed"}  # never counted

    # Pending
    pending_count = orders_qs.filter(status__in=PENDING_STATUSES).count()

    # --- Total spent
    total_spent = get_total_spent(user)
        # --- Last order timestamp (if the field exists)
    has_created = "created_at" in {f.name for f in Order._meta.get_fields()}
    last_order_at = (
        orders_qs.order_by("-created_at").values_list("created_at", flat=True).first()
        if has_created else None
    )

    return {
        "orders_count": orders_count,
        "pending_orders_count": pending_count,
        "total_spent": total_spent,
        "currency": currency,
        "last_order_at": last_order_at,
    }

def _profile_payload(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    full_name = (f"{user.first_name} {user.last_name}".strip() or user.username)
    document = Document.objects.filter(user=user).first()
    document = DocumentSerializer(document).data
    return {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "full_name": full_name,
        "profile": ProfileSerializer(profile).data,
        "stats": _compute_stats(user),
        "document": document,
    }

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Get current user with profile & stats",
        responses={200: MeSerializer},
        examples=[OpenApiExample(
            "Me",
            value={
                "id": 1, "username": "admin", "first_name": "Binod", "last_name": "Shrestha",
                "email": "binod@example.com", "full_name": "Binod Shrestha",
                "profile": {
                    "avatar": "/media/avatars/me.jpg",
                    "phone": "+977-9800000000",
                    "address": "Satdobato, Lalitpur",
                    "city": "Bagmati Province",
                    "zip": "44700",
                    "created_at": "2025-10-10T12:00:00Z",
                    "updated_at": "2025-10-11T08:00:00Z"
                },
                "stats": {
                    "orders_count": 12,
                    "pending_orders_count": 1,
                    "wishlist_count": 7,
                    "total_spent": "45999.00",
                    "currency": "NPR",
                    "last_order_at": "2025-10-11T05:02:02.315883Z"
                },
                "document": {
                    "id": 1,
                    "user": 1,
                    "document": "/media/documents/verification/Bytecare_tech.jpg",
                    "created_at": "2025-10-10T12:00:00Z",
                    "updated_at": "2025-10-11T08:00:00Z"
                }
            }
        )]
    )
    def get(self, request):
        return Response(_profile_payload(request.user), status=200)

class ProfileMePatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    @extend_schema(
        summary="Update my profile (and name/email)",
        request=MeUpdateSerializer,
        responses={200: OpenApiResponse(response=MeSerializer, description="Updated details")},
    )
    def patch(self, request):
        ser = MeUpdateSerializer(data=request.data, partial=True)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        ser.save(user=request.user)
        return Response(_profile_payload(request.user), status=200)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="Change my password",
        request=ChangePasswordSerializer,
        responses={200: OpenApiResponse(description="Password changed")},
    )
    def post(self, request):
        ser = ChangePasswordSerializer(data=request.data, context={"request": request})
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        ser.save()
        return Response({"detail": "Password updated successfully."}, status=200)