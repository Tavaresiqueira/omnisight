import uuid
from django.conf import settings

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import APIException
from rest_framework import serializers
from identity.account_lifecycle import close_account, close_organization
from identity.deletion_ledger import append_deletions

from identity.models import Membership, Organization, Scan, Site, ScanReport, User
from identity.scans import transition_scan
from identity.abuse import client_ip, enqueue_scan
from identity.ssrf import DestinationBlocked, resolve_public_destination
from identity.serializers import (
    ScanRequestSerializer,
    ScanSerializer,
    DemoLoginSerializer,
    LoginSerializer,
    OrganizationSerializer,
    RegistrationSerializer,
    SiteSerializer,
    UserSerializer,
)


def auth_payload(user):
    membership = user.memberships.select_related("organization").order_by("created_at").first()
    token, _ = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "user": UserSerializer(user).data,
        "organization": OrganizationSerializer(membership.organization).data if membership else None,
        "role": membership.role if membership else None,
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]
    abuse_scope = 'register'

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(auth_payload(user), status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    abuse_scope = 'login'

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(auth_payload(serializer.validated_data["user"]))


class DemoLoginView(APIView):
    permission_classes = [AllowAny]
    abuse_scope = 'demo'

    def post(self, request):
        if not settings.DEMO_LOGIN_ENABLED:
            return Response(status=404)
        validator = DemoLoginSerializer(data=request.data)
        validator.is_valid(raise_exception=True)
        user = (
            Membership.objects.filter(
                user__is_demo=True,
                user__account_type=validator.validated_data["account_type"],
            )
            .select_related("user")
            .order_by("created_at")
            .first()
        )
        if not user:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(auth_payload(user.user))


class MeView(APIView):
    def get(self, request):
        return Response(auth_payload(request.user))


class OrganizationDetailView(APIView):
    abuse_scope = 'closure'

    def post(self, request, organization_id):
        get_object_or_404(Organization, id=organization_id, memberships__user=request.user)
        validator = ClosureSerializer(data=request.data)
        validator.is_valid(raise_exception=True)
        try:
            close_organization(request.user.id, organization_id, **validator.validated_data)
        except (User.DoesNotExist, Organization.DoesNotExist):
            return Response(status=404)
        except (OSError, ValueError):
            raise DeletionUnavailable()
        return Response(status=204)

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


class SitesView(APIView):
    abuse_scope = 'site'
    def get_organization(self, user):
        membership = (
            Membership.objects.filter(user=user)
            .select_related("organization")
            .order_by("created_at")
            .first()
        )
        return membership.organization if membership else None

    def problem(self, code, message, response_status):
        return Response(
            {
                "code": code,
                "message": message,
                "correlationId": str(uuid.uuid4()),
            },
            status=response_status,
        )

    def get(self, request):
        organization = self.get_organization(request.user)
        if not organization:
            return Response(status=status.HTTP_403_FORBIDDEN)

        sites = organization.sites.filter(deleted_at__isnull=True).order_by("-created_at")
        return Response({"items": SiteSerializer(sites, many=True).data, "nextCursor": None})

    def post(self, request):
        organization = self.get_organization(request.user)
        if not organization:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = SiteSerializer(data=request.data)
        if not serializer.is_valid():
            if "url" in serializer.errors:
                return self.problem(
                    "INVALID_URL",
                    str(serializer.errors["url"][0]),
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        normalized_url = serializer.validated_data["normalized_url"]
        try:
            resolve_public_destination(normalized_url)
        except DestinationBlocked as error:
            return self.problem(
                "DESTINATION_NOT_ALLOWED",
                str(error),
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if organization.sites.filter(
            normalized_url=normalized_url,
            deleted_at__isnull=True,
        ).exists():
            return self.problem(
                "SITE_ALREADY_EXISTS",
                "Este site já está cadastrado nesta organização.",
                status.HTTP_409_CONFLICT,
            )

        try:
            with transaction.atomic():
                site = serializer.save(organization=organization)
        except IntegrityError:
            if organization.sites.filter(
                normalized_url=normalized_url,
                deleted_at__isnull=True,
            ).exists():
                return self.problem(
                    "SITE_ALREADY_EXISTS",
                    "Este site já está cadastrado nesta organização.",
                    status.HTTP_409_CONFLICT,
                )
            raise

        return Response(SiteSerializer(site).data, status=status.HTTP_201_CREATED)


class RequestScanView(APIView):
    def get(self,request,site_id):
        site=get_object_or_404(Site,id=site_id,deleted_at__isnull=True,organization__memberships__user=request.user)
        return Response({'items':ScanSerializer(site.scans.order_by('-requested_at')[:20],many=True).data})

    def post(self, request, site_id):
        site = get_object_or_404(Site, id=site_id, deleted_at__isnull=True, organization__memberships__user=request.user)
        if not Membership.objects.filter(user=request.user,organization=site.organization,role__in=['owner','member']).exists():
            return Response(status=403)
        key = request.headers.get('Idempotency-Key', '')
        if not 16 <= len(key) <= 128 or not key.isascii() or not key.isprintable():
            return Response({'message': 'Idempotency-Key deve conter entre 16 e 128 caracteres ASCII imprimíveis.'}, status=400)
        validator = ScanRequestSerializer(data=request.data)
        validator.is_valid(raise_exception=True)
        scan = enqueue_scan(request.user, site, key, client_ip(request))
        if scan.site_id != site.id:
            return Response({'code': 'IDEMPOTENCY_CONFLICT', 'message': 'Esta chave já foi utilizada para outro site.'}, status=409)
        return Response(ScanSerializer(scan).data, status=202)


class ScanDetailView(APIView):
    def get(self, request, scan_id):
        scan = get_object_or_404(Scan, id=scan_id, organization__memberships__user=request.user)
        return Response(ScanSerializer(scan).data)

    def delete(self, request, scan_id):
        with transaction.atomic():
            scan = get_object_or_404(Scan.objects.select_for_update(of=('self',)), id=scan_id, organization__memberships__user=request.user)
            if not Membership.objects.filter(user=request.user, organization=scan.organization, role='owner').exists():
                return Response(status=403)
            try:
                append_deletions([('scan', scan.id)])
            except (OSError, ValueError):
                raise DeletionUnavailable()
            # Deleting the parent row fences publication using the existing CAS.
            scan.delete()
        return Response(status=204)


class DeletionUnavailable(APIException):
    status_code = 503
    default_detail = 'Não foi possível registrar a exclusão com segurança. Tente novamente mais tarde.'


class ClosureSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=256)
    confirmation = serializers.CharField(max_length=120, trim_whitespace=False)


class AccountClosureView(APIView):
    abuse_scope = 'closure'

    def post(self, request):
        validator = ClosureSerializer(data=request.data)
        validator.is_valid(raise_exception=True)
        if validator.validated_data['confirmation'] != 'ENCERRAR MINHA CONTA':
            return Response({'message': 'Digite ENCERRAR MINHA CONTA para confirmar.'}, status=400)
        try:
            close_account(request.user.id, validator.validated_data['password'])
        except User.DoesNotExist:
            return Response(status=404)
        except (OSError, ValueError):
            raise DeletionUnavailable()
        return Response(status=204)


class AccountExportView(APIView):
    def get(self, request):
        return Response({'schemaVersion': 1, 'user': UserSerializer(request.user).data,
            'memberships': [{'organization': OrganizationSerializer(m.organization).data, 'role': m.role}
                for m in request.user.memberships.select_related('organization').order_by('created_at')],
            'reportExport': 'Exporte os relatórios autorizados separadamente na lista de scans.'})


class ScanReportView(APIView):
    def get(self,request,scan_id):
        report=get_object_or_404(ScanReport,scan_id=scan_id,scan__status='completed',scan__organization__memberships__user=request.user)
        return Response(report.payload)


class ScanActionView(APIView):
    def post(self,request,scan_id):
        scan=get_object_or_404(Scan,id=scan_id,organization__memberships__user=request.user)
        action=request.data.get('action')
        if action not in {'cancel','retry'}:
            return Response({'message':'Ação inválida.'},status=400)
        if not Membership.objects.filter(user=request.user,organization=scan.organization,role__in=['owner','member']).exists():
            return Response(status=403)
        try:
            scan = transition_scan(scan.id, 'cancelled') if action == 'cancel' else enqueue_scan(request.user, scan.site, scan.idempotency_key, client_ip(request), retry_id=scan.id)
        except ValueError as error:
            return Response({'message':str(error)},status=409)
        return Response(ScanSerializer(scan).data)


class HealthView(APIView):
    permission_classes=[AllowAny]
    authentication_classes=[]
    throttle_classes=[]
    def get(self,request):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return Response({'status':'ok'})
