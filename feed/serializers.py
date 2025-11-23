# feed/serializers.py
from django.db import transaction
from rest_framework import serializers
from django.contrib.auth import get_user_model
from commerce.models import Product  # adjust import if your app label differs
from .models import Post, Comment
from decimal import Decimal

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(read_only=True, source="profile.avatar")
    class Meta:
        model = User
        fields = ["id", "username", "email", "avatar"]

class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Comment
        fields = ["id", "user", "text", "created_at"]
        read_only_fields = ["id", "user", "created_at"]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['post'] = self.context['post']
        return Comment.objects.create(**validated_data)

class PostSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)

    # ---- Write-only product fields (optional unless link_product=True) ----
    product_name  = serializers.CharField(
        required=False, write_only=True, allow_blank=False, max_length=255,
        help_text="Product name (required if link_product=true)."
    )
    product_price = serializers.DecimalField(
        required=False, write_only=True, max_digits=10, decimal_places=2,
        help_text="Product price (required if link_product=true)."
    )
    product_qty   = serializers.IntegerField(
        required=False, write_only=True, min_value=0,
        help_text="Product stock quantity (required if link_product=true)."
    )
    product_image = serializers.ImageField(
        required=False, write_only=True, allow_empty_file=False,
        help_text="Product image file (required if link_product=true)."
    )
    description = serializers.CharField(
        required=False, write_only=True, allow_blank=False, max_length=255,
        help_text="Product description (required if link_product=true)."
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "type",
            "caption",
            "post_media",
            "link_product",
            "product_name",
            "product_price",
            "product_qty",
            "product_image",
            "product_linked",
            "likes",
            "created_at",
            "comments",
            "description",
        ]
        read_only_fields = ["id", "likes", "created_at", "product_linked"]

    def _require_product_fields_if_linking(self, attrs):
        """Enforce presence of product_* fields when link_product is true."""
        if attrs.get("link_product", False):
            missing = []
            for f in ("product_name", "product_price", "product_qty", "product_image"):
                # attrs may not include a field if it's not posted
                if attrs.get(f, None) in (None, ""):
                    missing.append(f)
            if missing:
                raise serializers.ValidationError({
                    "non_field_errors": [
                        "When link_product is true, the following fields are required: "
                        + ", ".join(missing)
                    ]
                })

    def validate(self, attrs):
        self._require_product_fields_if_linking(attrs)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Extract product helper fields
        pname  = validated_data.pop("product_name", None)
        pprice = validated_data.pop("product_price", None)
        pqty   = validated_data.pop("product_qty", None)
        pimg   = validated_data.pop("product_image", None)
        pdesc  = validated_data.pop("description", None)

        # Set user from request
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            validated_data["user"] = request.user
        else:
            raise serializers.ValidationError({"user": ["Authentication required."]})

        # Create the post first
        post = Post.objects.create(**validated_data)

        # If linking, create Product and attach
        if validated_data.get("link_product", False):
            # Safety: values already validated as present
            product = Product.objects.create(
                name=pname,
                price=Decimal(pprice) if not isinstance(pprice, Decimal) else pprice,
                quantity=pqty,
                image=pimg,
                seller=post.user,
                description=pdesc
            )

            # Link on the post and also store product_id
            post.product_linked = product
            if hasattr(post, "product_id"):
                post.product_id = product.pk
            post.save(update_fields=["product_linked"] + (["product_id"] if hasattr(post, "product_id") else []))

        return post
    
    
class LikeResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    likes = serializers.IntegerField()

class CommentCreateRequestSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=500)