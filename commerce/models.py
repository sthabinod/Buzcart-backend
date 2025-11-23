
from django.db import models
from auths.models import User
import uuid
class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller= models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    in_stock = models.BooleanField(default=True)
    description = models.TextField()
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['-created_at']
class Cart(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
class CartItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class PaymentMethod(models.TextChoices):
    COD = "cod", "Cash on Delivery"
    PAYPAL = "paypal", "PayPal"

class OrderStatus(models.TextChoices):
    PENDING   = "pending", "Pending"
    CONFIRMED = "confirmed", "Confirmed"
    SHIPPED   = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELED  = "canceled", "Canceled"

class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")

    # Shipping Address (from your UI)
    full_name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    street = models.CharField(max_length=255)
    city = models.CharField(max_length=120)
    zip_code = models.CharField(max_length=20)

    # Payment & status
    payment_method = models.CharField(max_length=12, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    status = models.CharField(max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING)

    # Money (keep as Decimal in DB; show NPR in UI)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.id} • {self.user} • NPR {self.total}"

class OrderItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")

    # FK to your existing Product model
    product = models.ForeignKey("commerce.Product", on_delete=models.PROTECT, related_name="order_items")

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)  # captured at purchase time
    line_total = models.DecimalField(max_digits=12, decimal_places=2)  # snapshot: unit_price * quantity

    def __str__(self):
        return f"{self.product_id} x {self.quantity}"