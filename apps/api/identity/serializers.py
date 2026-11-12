from urllib.parse import urlsplit, urlunsplit

from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from rest_framework import serializers

from identity.models import Organization, Site, User, Scan
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


class SiteSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source="normalized_url", write_only=True, max_length=2048)
    displayName = serializers.CharField(source="display_name", max_length=120)
    normalizedUrl = serializers.CharField(source="normalized_url", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Site
        fields = ["id", "url", "displayName", "normalizedUrl", "createdAt"]

    def validate_url(self, value):
        value = value.strip()
        if any(character.isspace() for character in value):
            raise serializers.ValidationError("Informe uma URL HTTPS válida.")

        try:
            parts = urlsplit(value)
            hostname = parts.hostname
            port = parts.port
        except ValueError as error:
            raise serializers.ValidationError("Informe uma URL HTTPS válida.") from error

        if parts.scheme.lower() != "https" or not hostname:
            raise serializers.ValidationError(
                "A URL deve começar com https:// e incluir um domínio válido."
            )
        if parts.username is not None or parts.password is not None:
            raise serializers.ValidationError("A URL não pode incluir usuário ou senha.")

        try:
            normalized_host = hostname.rstrip(".").encode("idna").decode("ascii").lower()
        except UnicodeError as error:
            raise serializers.ValidationError("Informe um domínio válido.") from error
        if not normalized_host:
            raise serializers.ValidationError("Informe um domínio válido.")

        host_for_url = f"[{normalized_host}]" if ":" in normalized_host else normalized_host
        netloc = host_for_url if port in (None, 443) else f"{host_for_url}:{port}"
        normalized_url = urlunsplit(("https", netloc, parts.path or "/", parts.query, ""))
        try:
            URLValidator(schemes=["https"])(normalized_url)
        except DjangoValidationError as error:
            raise serializers.ValidationError("Informe uma URL HTTPS válida.") from error
        return normalized_url


class ScanRequestSerializer(serializers.Serializer):
    viewport = serializers.ChoiceField(choices=['desktop'], default='desktop')

    def to_internal_value(self, data):
        if isinstance(data, dict) and set(data) - {'viewport'}:
            raise serializers.ValidationError({'non_field_errors': ['Opções de scan desconhecidas.']})
        return super().to_internal_value(data)


class ScanSerializer(serializers.ModelSerializer):
    siteId = serializers.UUIDField(source='site_id')
    requestedAt = serializers.DateTimeField(source='requested_at')
    startedAt = serializers.DateTimeField(source='started_at', allow_null=True)
    completedAt = serializers.DateTimeField(source='completed_at', allow_null=True)
    correlationId = serializers.UUIDField(source='correlation_id')

    errorCode = serializers.CharField(source='error_code')
    attempts = serializers.IntegerField()

    class Meta:
        model = Scan
        fields = ['errorCode', 'attempts', 'id', 'siteId', 'status', 'requestedAt', 'startedAt', 'completedAt', 'correlationId']
