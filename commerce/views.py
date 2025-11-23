# commerce/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .models import Product, Cart, CartItem, Order, OrderItem
from .serializers import (
    ProductSerializer, CartSerializer,
    CartAddItemIn,
    CheckoutResponseSerializer,
    CartItemQuantityPatchSerializer,
    CartItemSerializer,
    OrderSerializer,
    OrderCreateSerializer,
)
from django.db import transaction
# NEW: drf-spectacular helpers
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiResponse
)
from drf_spectacular.types import OpenApiTypes

class ProductListCreate(APIView):
    @extend_schema(
        summary="List products",
        responses={200: ProductSerializer(many=True)}
    )
    def get(self, request):
        return Response(ProductSerializer(Product.objects.all(), many=True).data)

class ProductDetail(APIView):
    @extend_schema(
        summary="Retrieve product",
        responses={200: ProductSerializer, 404: OpenApiResponse(description="Not found")}
    )
    def get(self, request, pk):
        obj = get_object_or_404(Product, pk=pk)
        return Response(ProductSerializer(obj).data)

    @extend_schema(
        summary="Update product (partial)",
        request=ProductSerializer,
        responses={200: ProductSerializer, 400: OpenApiResponse(description="Validation error"), 404: OpenApiResponse(description="Not found")}
    )
    def put(self, request, pk):
        obj = get_object_or_404(Product, pk=pk)
        ser = ProductSerializer(obj, data=request.data, partial=True)
        if ser.is_valid():
            ser.save()
            return Response(ser.data)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete product",
        responses={204: OpenApiResponse(description="Deleted"), 404: OpenApiResponse(description="Not found")}
    )
    def delete(self, request, pk):
        obj = get_object_or_404(Product, pk=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

def _get_or_create_active_cart(user):
    cart = Cart.objects.filter(user=user, is_active=True).first()
    if not cart:
        cart = Cart.objects.create(user=user, is_active=True)
    return cart

class ActiveCartView(APIView):
    @extend_schema(
        summary="Get active cart for a user",
        responses={200: CartSerializer, 400: OpenApiResponse(description="user_id is required")}
    )
    def get(self, request):
        user = request.user
        cart = _get_or_create_active_cart(user)
        return Response(CartSerializer(cart).data)

    @extend_schema(
        summary="Add item to active cart",
        request=CartAddItemIn,
        responses={201: CartSerializer, 400: OpenApiResponse(description="Validation error")}
    )
    def post(self, request):
        user= request.user
        product = request.data.get("product")
        product_obj = Product.objects.get(id=product)
        quantity = int(request.data.get("quantity", 1))
        if not (user and product):
            return Response({"detail":"user and product are required"}, status=400)
        cart = _get_or_create_active_cart(user)
        
        item = CartItem.objects.filter(cart=cart, product_id=product).first()
        if item:
            if product_obj.quantity < quantity:
                return Response({"detail":"Not enough stock"}, status=400)
            item.quantity += quantity
            item.save()
        else:
            if product_obj.quantity < quantity:
                return Response({"detail":"Not enough stock"}, status=400)
            CartItem.objects.create(cart=cart, product_id=product, quantity=quantity)
        return Response(CartSerializer(cart).data, status=201)

    @extend_schema(
        summary="Update ONLY quantity for a cart item",
        description="PATCH supports only 'quantity'. Identify the line by 'product' or 'id'.",
        request=CartItemQuantityPatchSerializer,
        responses={200: CartItemSerializer, 400: OpenApiResponse(description="Validation error"), 404: OpenApiResponse(description="Not found")}
    )
    def patch(self, request):
        cart = _get_or_create_active_cart(request.user)

        # Choose one lookup style. Example below uses 'product' sent in body.
        product_id = request.data.get("product")
        if not product_id:
            return Response({"detail": "product is required"}, status=400)

        item = get_object_or_404(CartItem, cart=cart, product_id=product_id)

        # Only pass quantity to the patch serializer
        data = {"quantity": request.data.get("quantity")}
        if data["quantity"] is None:
            return Response({"detail": "quantity is required"}, status=400)

        ser = CartItemQuantityPatchSerializer(instance=item, data=data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()

        # Return the full item using your read serializer
        return Response(CartItemSerializer(item, context={"request": request}).data, status=200)
    @extend_schema(
        summary="Remove item from active cart by cart item ID",
        parameters=[
            OpenApiParameter(
                name="cart_id",
                description="Cart item ID to delete",
                required=True,
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
        ),
        ],
        responses={200: CartSerializer, 400: OpenApiResponse(description="Missing or invalid parameters")},
    )
    def delete(self, request):
        user = request.user
        cart_id = request.query_params.get("cart_id")

        if not cart_id:
            return Response({"detail": "Cart ID is required (use ?cart_id=... in URL)"}, status=400)

        cart = _get_or_create_active_cart(user)

        deleted, _ = CartItem.objects.filter(cart=cart, id=cart_id).delete()
        if not deleted:
            return Response({"detail": "Cart item not found."}, status=404)

        return Response(CartSerializer(cart).data, status=200)

class CheckoutStub(APIView):
    @extend_schema(
        summary="Create draft order from active cart (no payment)",
        request=None,
        responses={201: CheckoutResponseSerializer, 400: OpenApiResponse(description="Validation error")}
    )
    def post(self, request):
        cart = _get_or_create_active_cart(request.user)
        total = 0.0
        items = []
        for it in cart.items.select_related('product').all():
            line_total = float(it.product.price) * it.quantity
            total += line_total
            items.append({
                "product_id": str(it.product_id),
                "name": it.product.name,
                "qty": it.quantity,
                "unit_price": float(it.product.price),
                "line_total": line_total,
            })
        cart.is_active = False
        cart.save()
        return Response({"user_id": request.user.id, "items": items, "total": total, "status": "pending_payment"}, status=201)

# ORDER RELATED


class OrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List my orders",
        tags=["Orders"],
        responses={200: OrderSerializer},
    )
    def get(self, request):
        qs = Order.objects.filter(user=request.user).order_by("-created_at")
        return Response(OrderSerializer(qs, many=True).data)

    @extend_schema(
        summary="Create an order",
        request=OrderCreateSerializer,
        tags=["Orders"],
        responses={201: OrderSerializer, 400: OpenApiResponse(description="Validation error")},
    )
    @transaction.atomic
    def post(self, request):
        ser = OrderCreateSerializer(data=request.data, context={"request": request})
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        order = ser.save()
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Get my order by id",
        tags=["Orders"],
        responses={200: OrderSerializer, 404: OpenApiResponse(description="Not found")})
    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)
        return Response(OrderSerializer(order).data)