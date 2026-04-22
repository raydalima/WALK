from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Modelo de usuário customizado com tipo de usuário"""

    class UserType(models.TextChoices):
        ALUNO = 'ALUNO', _('Aluno')
        PROFESSOR = 'PROFESSOR', _('Professor')
        ADMIN = 'ADMIN', _('Administrativo')

    email = models.EmailField(
        _('endereço de e-mail'),
        unique=True,
    )
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.ALUNO,
        verbose_name='Tipo de Usuário',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Telefone',
    )
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        verbose_name='Foto de Perfil',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_at']

    def __str__(self):
        name = self.get_full_name()
        utype = self.get_user_type_display()
        return f"{name} ({utype})"

    def is_student(self):
        return self.user_type == self.UserType.ALUNO

    def is_teacher(self):
        return self.user_type == self.UserType.PROFESSOR

    def is_admin_user(self):
        return self.user_type == self.UserType.ADMIN or self.is_superuser
