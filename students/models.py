from django.db import models
from django.conf import settings
from django.utils import timezone


class Student(models.Model):
    """Modelo para perfil de aluno com informações detalhadas"""

    class Status(models.TextChoices):
        CURSANDO = 'CURSANDO', 'Cursando'
        APROVADO = 'APROVADO', 'Aprovado'
        INATIVO = 'INATIVO', 'Inativo'
        EVADIDO = 'EVADIDO', 'Evadido'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='Usuário',
    )
    birth_date = models.DateField(
        verbose_name='Data de Nascimento',
        null=True,
        blank=True,
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        verbose_name='CPF',
        null=True,
        blank=True,
    )
    rg = models.CharField(max_length=20, verbose_name='RG', blank=True)

    # Endereço
    address = models.CharField(
        max_length=255,
        verbose_name='Endereço',
        blank=True,
    )
    city = models.CharField(max_length=100, verbose_name='Cidade', blank=True)
    state = models.CharField(max_length=2, verbose_name='Estado', blank=True)
    zip_code = models.CharField(max_length=10, verbose_name='CEP', blank=True)

    # Informações acadêmicas
    enrollment_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de Matrícula',
        null=True,
        blank=True,
    )
    enrollment_date = models.DateField(
        auto_now_add=True,
        verbose_name='Data de Matrícula',
    )

    # Contato de emergência
    emergency_contact_name = models.CharField(
        max_length=100,
        verbose_name='Nome do Contato de Emergência',
        blank=True,
    )
    emergency_contact_phone = models.CharField(
        max_length=20,
        verbose_name='Telefone do Contato de Emergência',
        blank=True,
    )
    responsible_name = models.CharField(
        max_length=150,
        verbose_name='Nome do Responsável',
        blank=True,
    )
    responsible_email = models.EmailField(
        verbose_name='E-mail do responsável',
        blank=True,
    )
    responsible_phone = models.CharField(
        max_length=30,
        verbose_name='Telefone do Responsável',
        blank=True,
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CURSANDO,
        verbose_name='Situação Acadêmica',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    notes = models.TextField(blank=True, verbose_name='Observações')
    approved_course = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Curso em que foi aprovado',
    )
    exit_reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Motivo de saída',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em',
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em',
    )

    class Meta:
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'
        ordering = ['-enrollment_date']

    def __str__(self):
        name = self.user.get_full_name()
        matricula = self.enrollment_number or 'Sem matrícula'
        return f"{name} - {matricula}"

    def get_enrolled_courses(self):
        """Retorna todas as disciplinas em que o aluno está matriculado"""
        from courses.models import Enrollment

        return Enrollment.objects.filter(student=self, is_active=True)

    @property
    def is_currently_enrolled(self):
        return self.status == self.Status.CURSANDO and self.is_active

    @property
    def is_minor(self):
        if not self.birth_date:
            return False
        today = timezone.localdate()
        age = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age < 18


class StudentHistory(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='history_entries',
        verbose_name='Aluno',
    )
    title = models.CharField(max_length=120, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_history_entries',
        verbose_name='Registrado por',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Histórico do Aluno'
        verbose_name_plural = 'Históricos dos Alunos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.student} - {self.title}'


class StudentApproval(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name='Aluno',
    )
    vestibular = models.CharField(max_length=150, verbose_name='Vestibular')
    institution = models.CharField(max_length=200, verbose_name='Instituição')
    course_name = models.CharField(max_length=200, verbose_name='Curso')
    approval_year = models.PositiveIntegerField(verbose_name='Ano de Aprovação')
    notes = models.TextField(blank=True, verbose_name='Observações')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_approvals_created',
        verbose_name='Registrado por',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Aprovação do Aluno'
        verbose_name_plural = 'Aprovações dos Alunos'
        ordering = ['-approval_year', '-created_at']

    def __str__(self):
        return (
            f'{self.student} - {self.institution} - '
            f'{self.course_name} ({self.approval_year})'
        )


class PreRegistration(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    course_interest = models.CharField(max_length=150, blank=True)

    class Gender(models.TextChoices):
        FEMININO = 'F', 'Feminino'
        MASCULINO = 'M', 'Masculino'
        NAO_BINARIO = 'NB', 'Não-binário'
        OUTRO = 'O', 'Outro'
        NAO_INFORMAR = 'NI', 'Prefiro não informar'

    class Race(models.TextChoices):
        BRANCA = 'BR', 'Branca'
        PRETA = 'PR', 'Preta'
        PARDA = 'PA', 'Parda'
        AMARELA = 'AM', 'Amarela'
        INDIGENA = 'IN', 'Indígena'
        NAO_DECLARAR = 'ND', 'Prefiro não declarar'

    class SchoolSituation(models.TextChoices):
        CURSANDO = 'CUR', 'Cursando'
        CONCLUIDO = 'CON', 'Concluído'
        TRANCADO = 'TRA', 'Trancado/Interrompido'
        OUTRO = 'OUT', 'Outro'

    class SchoolType(models.TextChoices):
        PUBLICA = 'PUB', 'Pública'
        PRIVADA = 'PRI', 'Privada'
        MISTA = 'MIS', 'Mista'
        NAO_INFORMAR = 'NI', 'Prefiro não informar'

    class YesNo(models.TextChoices):
        SIM = 'S', 'Sim'
        NAO = 'N', 'Não'

    class HousingStatus(models.TextChoices):
        PROPRIA = 'PROPRIA', 'Moradia própria'
        ALUGADA = 'ALUGADA', 'Moradia alugada'
        CEDIDA = 'CEDIDA', 'Moradia cedida'
        COMPARTILHADA = 'COMPARTILHADA', 'Moradia compartilhada'
        OUTRA = 'OUTRA', 'Outra situação'

    class TransportationType(models.TextChoices):
        A_PE = 'A_PE', 'A pé'
        BICICLETA = 'BICICLETA', 'Bicicleta'
        ONIBUS = 'ONIBUS', 'Ônibus/transporte público'
        MOTO = 'MOTO', 'Moto'
        CARRO = 'CARRO', 'Carro'
        OUTRO = 'OUTRO', 'Outro'

    class StudyHours(models.TextChoices):
        ATE_5 = 'ATE_5', 'Até 5 horas por semana'
        DE_6_A_10 = 'DE_6_A_10', 'De 6 a 10 horas por semana'
        DE_11_A_15 = 'DE_11_A_15', 'De 11 a 15 horas por semana'
        MAIS_15 = 'MAIS_15', 'Mais de 15 horas por semana'

    class IncomeRange(models.TextChoices):
        ATE_1 = 'ATE1', 'Até 1 salário mínimo'
        UM_A_DOIS = '1A2', 'De 1 a 2 salários mínimos'
        DOIS_A_TRES = '2A3', 'De 2 a 3 salários mínimos'
        TRES_A_CINCO = '3A5', 'De 3 a 5 salários mínimos'
        ACIMA_5 = 'A5', 'Acima de 5 salários mínimos'
        NAO_INFORMAR = 'NI', 'Prefiro não informar'

    gender = models.CharField(
        max_length=2,
        choices=Gender.choices,
        blank=True,
        default='',
    )
    race_self_declaration = models.CharField(
        max_length=2,
        choices=Race.choices,
        blank=True,
        default='',
    )
    pronouns = models.CharField(max_length=50, blank=True, default='')
    school_situation = models.CharField(
        max_length=3,
        choices=SchoolSituation.choices,
        blank=True,
        default='',
    )
    school_type = models.CharField(
        max_length=3,
        choices=SchoolType.choices,
        blank=True,
        default='',
    )
    has_taken_enem = models.CharField(
        max_length=1,
        choices=YesNo.choices,
        blank=True,
        default='',
    )
    family_income_range = models.CharField(
        max_length=4,
        choices=IncomeRange.choices,
        blank=True,
        default='',
    )
    has_internet_at_home = models.CharField(
        max_length=1,
        choices=YesNo.choices,
        blank=True,
        default='',
    )

    # Dados pessoais adicionais
    social_name = models.CharField(max_length=150, blank=True, default='')
    birth_date = models.DateField(null=True, blank=True)
    cpf = models.CharField(max_length=11, blank=True, default='')
    rg = models.CharField(max_length=30, blank=True, default='')
    address = models.CharField(max_length=255, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    state = models.CharField(max_length=2, blank=True, default='')
    zip_code = models.CharField(max_length=12, blank=True, default='')

    responsible_name = models.CharField(max_length=150, blank=True, default='')
    responsible_email = models.EmailField(blank=True, default='')
    responsible_phone = models.CharField(max_length=30, blank=True, default='')

    # Campos adicionais do responsável (para menores de 18 anos)
    responsible_cpf = models.CharField(max_length=11, blank=True, default='')
    responsible_rg = models.CharField(max_length=30, blank=True, default='')
    responsible_address = models.CharField(
        max_length=255,
        blank=True,
        default='',
    )

    class ResponsibleRelationship(models.TextChoices):
        MAE = 'MAE', 'Mãe'
        PAI = 'PAI', 'Pai'
        RESPONSAVEL = 'RES', 'Responsável'
        OUTRO = 'OUT', 'Outro'

    responsible_relationship = models.CharField(
        max_length=3,
        choices=ResponsibleRelationship.choices,
        blank=True,
        default='',
    )
    responsible_relationship_other = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )

    # Escolar
    graduation_year = models.CharField(max_length=10, blank=True, default='')
    intended_course = models.CharField(max_length=150, blank=True, default='')

    # Socioeconômico
    household_members = models.PositiveIntegerField(null=True, blank=True)
    has_device = models.CharField(max_length=1, blank=True, default='')
    works_currently = models.CharField(max_length=1, blank=True, default='')
    receives_social_benefit = models.CharField(
        max_length=1,
        choices=YesNo.choices,
        blank=True,
        default='',
    )
    has_private_study_space = models.CharField(
        max_length=1,
        choices=YesNo.choices,
        blank=True,
        default='',
    )
    transportation_type = models.CharField(
        max_length=20,
        choices=TransportationType.choices,
        blank=True,
        default='',
    )
    housing_status = models.CharField(
        max_length=20,
        choices=HousingStatus.choices,
        blank=True,
        default='',
    )
    weekly_study_hours = models.CharField(
        max_length=20,
        choices=StudyHours.choices,
        blank=True,
        default='',
    )

    # Divulgação e motivação
    how_did_you_hear = models.CharField(max_length=255, blank=True, default='')
    why_join = models.TextField(blank=True, default='')

    consent = models.BooleanField(default=False)
    is_reviewed = models.BooleanField(default=False)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} <{self.email}>'
