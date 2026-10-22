from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers

from identity.models import Organization, User
from identity.services import create_user_workspace


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "display_name", "account_type", "is_demo"]


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "account_type"]


class RegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    display_name = serializers.CharField(max_length=120)
    account_type = serializers.ChoiceField(choices=User.AccountType.choices)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return normalized

    def validate(self, attrs):
        candidate = User(
            email=attrs.get("email", ""),
            display_name=attrs.get("display_name", ""),
            account_type=attrs.get("account_type", ""),
        )
        password_validation.validate_password(attrs["password"], user=candidate)
        return attrs

    def create(self, validated_data):
        user, _ = create_user_workspace(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"].strip().lower(),
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("E-mail ou senha inválidos.")
        if not user.is_active:
            raise serializers.ValidationError("Esta conta está desativada.")
        attrs["user"] = user
        return attrs


class DemoLoginSerializer(serializers.Serializer):
    account_type = serializers.ChoiceField(choices=User.AccountType.choices)
