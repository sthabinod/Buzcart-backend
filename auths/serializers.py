
from rest_framework import serializers
from django.contrib.auth.models import User
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Profile
from verification.models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            "id", "user", "doc_type", "doc_file", "status", "created_at",
        ]
        read_only_fields = ["created_at"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "password", "confirm_password"]

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")  # remove before creating
        user = User(
            username=validated_data["username"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", "")
        )
        user.set_password(validated_data["password"])
        user.save()
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # 👇 Add custom claims here
        token['username'] = user.username
        token['email'] = user.email  # optional
        if Profile.objects.filter(user=user).exists():
            token['avatar'] = user.profile.avatar.url
        
        if Document.objects.filter(user=user).exists():
            if Document.objects.filter(user=user).first().status == 'approved':
                token['has_document'] = True
            else:
                token['has_document'] = False
        else:
            token['has_document'] = False
        return token
    
    
    
# Profile Serializer 
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "avatar", "phone", "address", "city", "zip",
            "created_at", "updated_at", 
        ]
        read_only_fields = ["created_at", "updated_at"]

class MeSerializer(serializers.Serializer):
    # user core
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    # profile
    profile = ProfileSerializer(read_only=True)
    documents = DocumentSerializer(read_only=True, source="user.documents")

    # stats (read-only)
    stats = serializers.DictField(read_only=True)

class MeUpdateSerializer(serializers.Serializer):
    # user edits
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name  = serializers.CharField(required=False, allow_blank=True, max_length=150)
    email      = serializers.EmailField(required=False, allow_blank=True)

    # profile edits
    phone   = serializers.CharField(required=False, allow_blank=True, max_length=15)
    address = serializers.CharField(required=False, allow_blank=True)
    city    = serializers.CharField(required=False, allow_blank=True, max_length=100)
    zip     = serializers.CharField(required=False, allow_blank=True, max_length=10)
    avatar  = serializers.ImageField(required=False, allow_null=True)

    def save(self, *, user):
        # Update user
        changed = []
        for f in ("first_name", "last_name", "email"):
            if f in self.validated_data:
                setattr(user, f, self.validated_data[f]); changed.append(f)
        if changed: user.save(update_fields=changed)

        # Update or create profile
        profile, _ = Profile.objects.get_or_create(user=user)
        p_changed = []
        for f in ("phone","address","city","zip","avatar"):
            if f in self.validated_data:
                setattr(profile, f, self.validated_data[f]); p_changed.append(f)
        if p_changed:
            from django.utils.timezone import now
            profile.updated_at = now()
            profile.save(update_fields=p_changed + ["updated_at"])
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, min_length=6, trim_whitespace=False)
    confirm_password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        user = self.context["request"].user
        if not user.check_password(attrs["old_password"]):
            raise serializers.ValidationError({"old_password": "Old password is incorrect."})
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user