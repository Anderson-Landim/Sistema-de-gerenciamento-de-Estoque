from django.core.management.base import BaseCommand
from almoxarifado.models import CustomUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class Command(BaseCommand):
    help = 'Cria um superusuário com categoria super_admin'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.MIGRATE_HEADING('=== Criar Super Admin ==='))

        username = input('Username: ')
        email = input('Email: ')
        
        while True:
            password = input('Senha: ')
            try:
                validate_password(password)
                break
            except ValidationError as e:
                self.stdout.write(self.style.ERROR('\n'.join(e.messages)))

        if CustomUser.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'Usuário "{username}" já existe!'))
            return

        user = CustomUser.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            categoria='super_admin'
        )
        self.stdout.write(self.style.SUCCESS(f'Super Admin "{username}" criado com sucesso!'))
