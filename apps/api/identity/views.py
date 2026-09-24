from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from identity.models import Membership, Organization
from identity.serializers import (
    LoginSerializer,
    OrganizationSerializer,
    RegistrationSerializer,
    UserSerializer,
)


def auth_payload(user):
    membership = user.memberships.select_related("organization").order_by("created_at").first()
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "user": UserSerializer(user).data,
        "organization": OrganizationSerializer(membership.organization).data,
        "role": membership.role,
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(auth_payload(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(auth_payload(serializer.validated_data["user"]))


class MeView(APIView):
    def get(self, request):
        return Response(auth_payload(request.user))


class OrganizationDetailView(APIView):
    def get(self, request, organization_id):
        organization = get_object_or_404(
            Organization,
            id=organization_id,
            memberships__user=request.user,
        )
        membership = get_object_or_404(
            Membership,
            organization=organization,
            user=request.user,
        )
        return Response(
            {
                "organization": OrganizationSerializer(organization).data,
                "role": membership.role,
            }
        )

