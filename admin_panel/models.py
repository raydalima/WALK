from django.conf import settings
from django.db import models
from django.utils import timezone


class CommunicationCategory(models.TextChoices):
    GERAL = 'GERAL', 'Geral'
    PEDAGOGICO = 'PEDAGOGICO', 'Pedagógico'
    FREQUENCIA = 'FREQUENCIA', 'Frequência'
    ATIVIDADE = 'ATIVIDADE', 'Atividade'
    REUNIAO = 'REUNIAO', 'Reunião'
    EVENTO = 'EVENTO', 'Evento'
    ORIENTACAO = 'ORIENTACAO', 'Orientação'
    RESPONSAVEL = 'RESPONSAVEL', 'Responsável'
    PROFESSORES = 'PROFESSORES', 'Professores'


class Audience(models.TextChoices):
    TODOS = 'TODOS', 'Todos'
    ALUNOS = 'ALUNOS', 'Alunos'
    PROFESSORES = 'PROFESSORES', 'Professores'
    ADMINISTRATIVO = 'ADMINISTRATIVO', 'Administrativo'


class AdministrativeProfile(models.Model):
    class Role(models.TextChoices):
        COORDENACAO = 'COORDENACAO', 'Coordenação'
        SECRETARIA = 'SECRETARIA', 'Secretaria'
        APOIO = 'APOIO', 'Apoio Administrativo'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='administrative_profile',
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.APOIO,
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Perfil Administrativo'
        verbose_name_plural = 'Perfis Administrativos'

    def __str__(self):
        return f'{self.user.get_full_name()} ({self.get_role_display()})'


class EmailTemplate(models.Model):
    name = models.CharField(max_length=120, verbose_name='Nome')
    category = models.CharField(
        max_length=30,
        choices=CommunicationCategory.choices,
        default=CommunicationCategory.GERAL,
        verbose_name='Categoria',
    )
    default_subject = models.CharField(max_length=180, verbose_name='Assunto padrão')
    default_body = models.TextField(verbose_name='Corpo padrão')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_templates_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Modelo de E-mail'
        verbose_name_plural = 'Modelos de E-mail'
        ordering = ['category', 'name']

    def __str__(self):
        return self.name


class PanelNotice(models.Model):
    title = models.CharField(max_length=180, verbose_name='Título')
    summary = models.CharField(max_length=255, blank=True, verbose_name='Resumo')
    content = models.TextField(verbose_name='Conteúdo')
    category = models.CharField(
        max_length=30,
        choices=CommunicationCategory.choices,
        default=CommunicationCategory.GERAL,
        verbose_name='Categoria',
    )
    audience = models.CharField(
        max_length=20,
        choices=Audience.choices,
        default=Audience.TODOS,
        verbose_name='Público-alvo',
    )
    turma = models.ForeignKey(
        'courses.Turma',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='panel_notices',
        verbose_name='Turma específica',
    )
    is_featured = models.BooleanField(default=False, verbose_name='Destaque')
    is_visible = models.BooleanField(default=True, verbose_name='Visível')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='panel_notices_created',
        verbose_name='Criado por',
    )
    published_at = models.DateTimeField(verbose_name='Data de publicação')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Aviso do Painel'
        verbose_name_plural = 'Avisos do Painel'
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title


class CalendarEvent(models.Model):
    class EventType(models.TextChoices):
        AULA_ESPECIAL = 'AULA_ESPECIAL', 'Aula especial'
        SIMULADO = 'SIMULADO', 'Simulado'
        REVISAO = 'REVISAO', 'Revisão'
        REUNIAO = 'REUNIAO', 'Reunião'
        PRAZO_ATIVIDADE = 'PRAZO_ATIVIDADE', 'Prazo de atividade'
        REDACAO = 'REDACAO', 'Redação'
        OFICINA = 'OFICINA', 'Oficina'
        FERIADO = 'FERIADO', 'Feriado'
        INSTITUCIONAL = 'INSTITUCIONAL', 'Evento institucional'

    title = models.CharField(max_length=180, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        default=EventType.INSTITUCIONAL,
        verbose_name='Tipo de evento',
    )
    starts_at = models.DateTimeField(verbose_name='Início')
    ends_at = models.DateTimeField(null=True, blank=True, verbose_name='Fim')
    location = models.CharField(max_length=180, blank=True, verbose_name='Local')
    audience = models.CharField(
        max_length=20,
        choices=Audience.choices,
        default=Audience.TODOS,
        verbose_name='Público-alvo',
    )
    turma = models.ForeignKey(
        'courses.Turma',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendar_events',
        verbose_name='Turma específica',
    )
    is_featured = models.BooleanField(default=False, verbose_name='Destaque')
    is_visible = models.BooleanField(default=True, verbose_name='Visível no painel/blog')
    external_calendar_id = models.CharField(
        max_length=180,
        blank=True,
        verbose_name='ID externo do calendário',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='calendar_events_created',
        verbose_name='Criado por',
    )
    related_notice = models.ForeignKey(
        PanelNotice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='calendar_events',
        verbose_name='Aviso relacionado',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Evento do Calendário'
        verbose_name_plural = 'Eventos do Calendário'
        ordering = ['starts_at', 'title']

    def __str__(self):
        return self.title


class EmailCommunication(models.Model):
    class SendType(models.TextChoices):
        INDIVIDUAL = 'INDIVIDUAL', 'Individual'
        MASSA = 'MASSA', 'Em massa'

    class RecipientGroup(models.TextChoices):
        ALUNO = 'ALUNO', 'Aluno'
        PROFESSOR = 'PROFESSOR', 'Professor'
        RESPONSAVEL = 'RESPONSAVEL', 'Responsável'
        ALUNO_RESPONSAVEL = 'ALUNO_RESPONSAVEL', 'Aluno e responsável'
        TODOS_ALUNOS = 'TODOS_ALUNOS', 'Todos os alunos'
        TODOS_PROFESSORES = 'TODOS_PROFESSORES', 'Todos os professores'
        TODOS_RESPONSAVEIS = 'TODOS_RESPONSAVEIS', 'Todos os responsáveis'
        ALUNOS_TURMA = 'ALUNOS_TURMA', 'Alunos de uma turma'
        PROFESSORES_TURMA = 'PROFESSORES_TURMA', 'Professores de uma turma'
        ALUNOS_ATIVOS = 'ALUNOS_ATIVOS', 'Alunos ativos'
        ALUNOS_BAIXA_FREQUENCIA = 'ALUNOS_BAIXA_FREQUENCIA', 'Alunos com baixa frequência'
        ALUNOS_ATIVIDADE_PENDENTE = 'ALUNOS_ATIVIDADE_PENDENTE', 'Alunos com atividade pendente'

    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        AGENDADO = 'AGENDADO', 'Agendado'
        ENVIADO = 'ENVIADO', 'Enviado'
        PARCIAL = 'PARCIAL', 'Parcial'
        FALHOU = 'FALHOU', 'Falhou'

    subject = models.CharField(max_length=180, verbose_name='Assunto')
    message = models.TextField(verbose_name='Mensagem')
    category = models.CharField(
        max_length=30,
        choices=CommunicationCategory.choices,
        default=CommunicationCategory.GERAL,
        verbose_name='Categoria',
    )
    template = models.ForeignKey(
        EmailTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='communications',
        verbose_name='Modelo utilizado',
    )
    send_type = models.CharField(max_length=20, choices=SendType.choices)
    recipient_group = models.CharField(max_length=40, choices=RecipientGroup.choices)
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='email_communications_sent',
        verbose_name='Enviado por',
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name='Criado em')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='Data de Envio')
    scheduled_at = models.DateTimeField(null=True, blank=True, verbose_name='Data agendada')
    send_immediately = models.BooleanField(default=True, verbose_name='Enviar imediatamente')
    related_notice = models.ForeignKey(
        PanelNotice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_communications',
        verbose_name='Aviso relacionado',
    )
    related_event = models.ForeignKey(
        CalendarEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_communications',
        verbose_name='Evento relacionado',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
        verbose_name='Situação',
    )
    total_recipients = models.PositiveIntegerField(default=0)
    successful_recipients = models.PositiveIntegerField(default=0)
    failed_recipients = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Comunicação por E-mail'
        verbose_name_plural = 'Comunicações por E-mail'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} ({self.get_send_type_display()})'


class EmailCommunicationRecipient(models.Model):
    class RecipientType(models.TextChoices):
        ALUNO = 'ALUNO', 'Aluno'
        PROFESSOR = 'PROFESSOR', 'Professor'
        RESPONSAVEL = 'RESPONSAVEL', 'Responsável'

    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        ENVIADO = 'ENVIADO', 'Enviado'
        FALHOU = 'FALHOU', 'Falhou'
        SEM_EMAIL = 'SEM_EMAIL', 'Sem e-mail'

    communication = models.ForeignKey(
        EmailCommunication,
        on_delete=models.CASCADE,
        related_name='recipients',
        verbose_name='Comunicação',
    )
    email = models.EmailField(verbose_name='E-mail de destino')
    name = models.CharField(max_length=180, blank=True, verbose_name='Nome')
    recipient_type = models.CharField(max_length=20, choices=RecipientType.choices)
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_recipients',
    )
    teacher = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_recipients',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Destinatário de E-mail'
        verbose_name_plural = 'Destinatários de E-mail'
        ordering = ['name', 'email']

    def __str__(self):
        return f'{self.name or self.email} <{self.email}>'
