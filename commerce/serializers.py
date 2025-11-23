# commerce/serializers.py
from rest_framework import serializers
from .models import Product, Cart, CartItem
from rest_framework.exceptions import ValidationError
from django.db import transaction
from .models import PaymentMethod
from .models import OrderStatus
from decimal import Decimal
from .models import OrderItem,Order





class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.CharField(source='seller.username')
    class Meta:
        model = Product
        fields = ['id','seller','name','price','in_stock','description','image','quantity','created_at']
        read_only_fields = ['id','created_at']

class CartItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source='product', read_only=True)
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'quantity','product_details']
        
    def create(self, validated_data):
        print(validated_data)
        user = self.context['request'].user
        product = validated_data.get('product')
        quantity = validated_data.get('quantity')
        print(product)
        print(Product.objects.filter(id=product))
        if Product.objects.filter(id=product).exists():
            product_obj = Product.objects.get(id=product)
            print(product_obj)
        else:
            raise ValidationError({
                "product": "Product not found."
            })
        
        if product_obj.quantity < quantity:
            raise ValidationError({
                "quantity": f"Only {product_obj.quantity} items left in stock."
            })
        
        validated_data['cart'] = user.cart
        
        return CartItem.objects.create(**validated_data)



class CartItemQuantityPatchSerializer(serializers.ModelSerializer):
    """Used only for PATCH to update quantity."""
    quantity = serializers.IntegerField(min_value=1)
    product = serializers.UUIDField(required=True)

    class Meta:
        model = CartItem
        fields = ["quantity","product"]        
        read_only_fields = ["product"]

    def update(self, instance: CartItem, validated_data):
        new_qty = int(validated_data["quantity"])

        with transaction.atomic():
            # Lock both rows to avoid race conditions
            product = (Product.objects
                       .select_for_update()
                       .only("id", "quantity")
                       .get(id=instance.product_id))
            _locked_item = (CartItem.objects
                            .select_for_update()
                            .get(pk=instance.pk))

            if new_qty > product.quantity:
                raise ValidationError(
                    {"quantity": f"Not enough stock. Available: {product.quantity}."}
                )

            instance.quantity = new_qty
            instance.save(update_fields=["quantity"])

        return instance

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ['id','is_active','created_at','items']
        read_only_fields = ['id','is_active','created_at','items']

# ----- Swagger-only helper serializers -----
class CartAddItemIn(serializers.Serializer):
    product = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)

# class CheckoutRequestSerializer(serializers.Serializer):
#     user= serializers.UUIDField()

class CheckoutItemSerializer(serializers.Serializer):
    product_id = serializers.UUIDField()
    name = serializers.CharField()
    qty = serializers.IntegerField()
    unit_price = serializers.FloatField()
    line_total = serializers.FloatField()

class CheckoutResponseSerializer(serializers.Serializer):
    items = CheckoutItemSerializer(many=True)
    total = serializers.FloatField()
    status = serializers.ChoiceField(choices=["pending_payment"])



class OrderItemInSerializer(serializers.Serializer):
    product = serializers.UUIDField()            # product id (FK)
    quantity = serializers.IntegerField(min_value=1)

class OrderCreateSerializer(serializers.Serializer):
    # Address
    full_name = serializers.CharField(max_length=120)
    phone = serializers.CharField(max_length=32)
    street = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=120)
    zip_code = serializers.CharField(max_length=20)

    payment_method = serializers.ChoiceField(choices=PaymentMethod.choices, default=PaymentMethod.COD)

    # Optional pricing from client (we will re-compute server-side for trust)
    shipping = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=Decimal("0.00"))
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=Decimal("0.00"))

    items = OrderItemInSerializer(many=True)

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("At least one item is required.")
        return items

    def create(self, validated):
        user = self.context["request"].user
        shipping = validated.get("shipping", Decimal("0.00"))
        discount = validated.get("discount", Decimal("0.00"))

        # Fetch products and compute prices
        product_map = {}
        subtotal = Decimal("0.00")

        for it in validated["items"]:
            prod = Product.objects.select_for_update().get(pk=it["product"])
            if not prod.in_stock or prod.quantity < it["quantity"]:
                raise serializers.ValidationError(f"Insufficient stock for product '{prod.name}'.")
            product_map[it["product"]] = prod

        # Create order
        order = Order.objects.create(
            user=user,
            full_name=validated["full_name"],
            phone=validated["phone"],
            street=validated["street"],
            city=validated["city"],
            zip_code=validated["zip_code"],
            payment_method=validated["payment_method"],
            shipping=shipping,
            discount=discount,
        )

        # Items + stock decrement
        items_to_create = []
        for it in validated["items"]:
            prod = product_map[it["product"]]
            unit_price = prod.price
            line_total = unit_price * it["quantity"]
            subtotal += line_total
            items_to_create.append(OrderItem(
                order=order, product=prod, quantity=it["quantity"],
                unit_price=unit_price, line_total=line_total
            ))
            # reduce stock
            prod.quantity -= it["quantity"]
            prod.in_stock = prod.quantity > 0
            prod.save(update_fields=["quantity", "in_stock"])

        OrderItem.objects.bulk_create(items_to_create)

        order.subtotal = subtotal
        order.total = subtotal + shipping - discount
        order.save(update_fields=["subtotal", "total"])
        return order

class ProductMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "image", "price"]

class OrderItemOutSerializer(serializers.ModelSerializer):
    product_details = ProductMiniSerializer(source="product", read_only=True)
    class Meta:
        model = OrderItem
        fields = ["id", "product", "quantity", "unit_price", "line_total", "product_details"]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemOutSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = [
            "id", "created_at", "status",
            "full_name", "phone", "street", "city", "zip_code",
            "payment_method",
            "subtotal", "shipping", "discount", "total",
            "note",
            "items",
        ]