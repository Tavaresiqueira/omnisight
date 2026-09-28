import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from identity.models import User
from identity.services import create_user_workspace


DEMO_USERS = [
    {
        "email": "extension.demo@omnisight.local",
        "display_name": "Demo Extensão",
        "account_type": User.AccountType.EXTENSION_USER,
        "organization_name": "Experiência acessível — Demo",
    },
    {
        "email": "developer.demo@omnisight.local",
        "display_name": "Demo Plataforma",
        "account_type": User.AccountType.PLATFORM_DEVELOPER,
        "organization_name": "Plataforma acessível — Demo",
    },
]


class Command(BaseCommand):
    help = "Cria as duas contas demo do MVP de forma idempotente."

    def handle(self, *args, **options):
        password = os.environ.get("OMNISIGHT_DEMO_PASSWORD")
        if not password and settings.DEBUG:
            password = "Demo-OmniSight-2026!"
        if not password:
            raise CommandError("Defina OMNISIGHT_DEMO_PASSWORD fora do modo DEBUG.")

        for demo in DEMO_USERS:
            user = User.objects.filter(email=demo["email"]).first()
            if not user:
                user, _ = create_user_workspace(
                    password=password,
                    is_demo=True,
                    **demo,
                )
                action = "criada"
            else:
                user.display_name = demo["display_name"]
                user.account_type = demo["account_type"]
                user.is_demo = True
                user.set_password(password)
                user.save(
                    update_fields=["display_name", "account_type", "is_demo", "password"]
                )
                action = "atualizada"
            self.stdout.write(self.style.SUCCESS(f"Conta {demo['email']} {action}."))

