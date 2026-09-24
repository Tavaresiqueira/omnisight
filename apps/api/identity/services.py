import uuid

from django.db import transaction
from django.utils.text import slugify

from identity.models import Membership, Organization, User


@transaction.atomic
def create_user_workspace(
    *,
    email,
    password,
    display_name,
    account_type,
    is_demo=False,
    organization_name=None,
):
    user = User.objects.create_user(
        email=email,
        password=password,
        display_name=display_name,
        account_type=account_type,
        is_demo=is_demo,
    )
    name = organization_name or f"Espaço de {display_name}"
    slug_base = slugify(name)[:60] or "workspace"
    organization = Organization.objects.create(
        name=name,
        slug=f"{slug_base}-{uuid.uuid4().hex[:8]}",
        account_type=account_type,
    )
    Membership.objects.create(
        organization=organization,
        user=user,
        role=Membership.Role.OWNER,
    )
    return user, organization

