from django.db import transaction
from rest_framework.exceptions import APIException, PermissionDenied, ValidationError
from identity.deletion_ledger import append_deletions
from identity.models import Membership, Organization, Scan, User


class ClosureConflict(APIException):
    status_code = 409
    default_detail = 'Você é o único proprietário de um espaço compartilhado. Encerre esse espaço explicitamente ou transfira a propriedade antes de encerrar a conta.'


def verify_password(user, password):
    if user.is_demo:
        raise PermissionDenied('Contas demo compartilhadas não podem ser encerradas aqui.')
    if not user.check_password(password):
        raise ValidationError({'message': 'Senha atual incorreta.'})


@transaction.atomic
def close_account(user_id, password):
    user = User.objects.select_for_update().get(id=user_id)
    verify_password(user, password)
    organizations = list(Organization.objects.select_for_update().filter(memberships__user=user).order_by('id'))
    exclusive = []
    for organization in organizations:
        membership = Membership.objects.get(user=user, organization=organization)
        others = organization.memberships.exclude(user=user)
        if membership.role == 'owner' and not others.filter(role='owner').exists():
            if others.exists():
                raise ClosureConflict()
            exclusive.append(organization.id)
    # Lock before cascade to fence concurrent report publication.
    list(Scan.objects.select_for_update().filter(organization_id__in=exclusive).order_by('id').values_list('id', flat=True))
    append_deletions([('organization', target) for target in exclusive] + [('user', user.id)])
    Organization.objects.filter(id__in=exclusive).delete()
    user.delete()  # Also revokes all DRF tokens and Django sessions no longer authenticate.


@transaction.atomic
def close_organization(user_id, organization_id, password, confirmation):
    user = User.objects.select_for_update().get(id=user_id)
    verify_password(user, password)
    organization = Organization.objects.select_for_update().get(id=organization_id)
    if not Membership.objects.filter(user=user, organization=organization, role='owner').exists():
        raise PermissionDenied('Somente o proprietário pode encerrar o espaço.')
    if confirmation != organization.name:
        raise ValidationError({'message': 'Digite exatamente o nome do espaço para confirmar.'})
    list(Scan.objects.select_for_update().filter(organization=organization).order_by('id').values_list('id', flat=True))
    append_deletions([('organization', organization.id)])
    organization.delete()
