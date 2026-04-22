from django.conf import settings
from django.db import models
from utils.external_links import validate_external_resource_url


class Quiz(models.Model):
    course = models.ForeignKey(
        'courses.Disciplina',
        on_delete=models.CASCADE,
        related_name='quizzes',
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_quizzes',
    )

    is_published = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.title} ({self.course_id})'


class Question(models.Model):
    class QuestionType(models.TextChoices):
        MULTIPLE_CHOICE = 'MCQ', 'Múltipla escolha'
        TRUE_FALSE = 'TF', 'Verdadeiro/Falso'
        SHORT_TEXT = 'ST', 'Resposta curta'
        ESSAY = 'ES', 'Redação/Discursiva'

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
    )
    text = models.TextField()
    type = models.CharField(
        max_length=3,
        choices=QuestionType.choices,
        default=QuestionType.MULTIPLE_CHOICE,
    )
    order = models.PositiveIntegerField(default=0)
    points = models.DecimalField(max_digits=6, decimal_places=2, default=1)

    # Para respostas curtas (opcional)
    correct_text = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self) -> str:
        return f'Q{self.id} - {self.quiz_id}'


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='choices',
    )
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.text


class Submission(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Rascunho'
        SUBMITTED = 'SUB', 'Enviado'
        GRADED = 'GRD', 'Corrigido'

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='submissions',
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='quiz_submissions',
    )

    attempt = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=5,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name='Situação',
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    corrected_at = models.DateTimeField(null=True, blank=True)
    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='corrected_submissions',
    )

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['quiz', 'student', 'attempt']),
        ]

    def __str__(self) -> str:
        return (
            f'Submission {self.id} - {self.quiz_id} - '
            f'{self.student_id} (#{self.attempt})'
        )


class Answer(models.Model):
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
    )

    selected_choice = models.ForeignKey(
        Choice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    text_answer = models.TextField(blank=True)

    auto_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    teacher_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    teacher_feedback = models.TextField(blank=True)

    class Meta:
        unique_together = [('submission', 'question')]

    def __str__(self) -> str:
        return (
            f'Answer {self.id} (submission={self.submission_id}, '
            f'question={self.question_id})'
        )


class Activity(models.Model):
    class Status(models.TextChoices):
        RASCUNHO = 'RASCUNHO', 'Rascunho'
        PUBLICADA = 'PUBLICADA', 'Publicada'
        ENCERRADA = 'ENCERRADA', 'Encerrada'

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    turma = models.ForeignKey(
        'courses.Turma',
        on_delete=models.CASCADE,
        related_name='activities',
    )
    area = models.ForeignKey(
        'courses.AreaConhecimento',
        on_delete=models.SET_NULL,
        related_name='activities',
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        'courses.Disciplina',
        on_delete=models.CASCADE,
        related_name='activities',
        null=True,
        blank=True,
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='activities_led',
        null=True,
        blank=True,
    )
    due_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_activities',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.RASCUNHO,
        verbose_name='Situação',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ActivityResult(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        ENVIADA = 'ENVIADA', 'Enviada'
        EM_CORRECAO = 'EM_CORRECAO', 'Em correção'
        CORRIGIDA = 'CORRIGIDA', 'Corrigida'
        REVISAO_SOLICITADA = 'REVISAO_SOLICITADA', 'Revisão solicitada'
        NAO_ENTREGUE = 'NAO_ENTREGUE', 'Não entregue'
        FEZ = 'FEZ', 'Fez'
        ENTREGUE = 'ENTREGUE', 'Entregue'
        NAO_FEZ = 'NAO_FEZ', 'Não fez'
        AUSENTE = 'AUSENTE', 'Ausente'

    activity = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name='results',
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='activity_results',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
        verbose_name='Situação',
    )
    submission_url = models.URLField(
        blank=True,
        verbose_name='Link de envio',
        help_text='Link do Google Docs, Drive, Dropbox ou outra nuvem.',
    )
    notes = models.TextField(blank=True, verbose_name='Observação do aluno')
    teacher_feedback = models.TextField(blank=True, verbose_name='Feedback do professor')
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Nota',
    )
    submitted_at = models.DateTimeField(null=True, blank=True, verbose_name='Data de envio')
    corrected_at = models.DateTimeField(null=True, blank=True, verbose_name='Data de correção')
    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='corrected_activity_results',
        verbose_name='Professor responsável',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('activity', 'student')]
        ordering = ['student_id']

    def __str__(self):
        return f'{self.activity} - {self.student} - {self.get_status_display()}'

    def clean(self):
        validate_external_resource_url(self.submission_url)


class EssaySubmission(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        SUBMITTED = 'SUBMITTED', 'Enviada'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Em correção'
        CORRECTED = 'CORRECTED', 'Corrigida'
        REVISAO_SOLICITADA = 'REVISAO_SOLICITADA', 'Revisão solicitada'
        NAO_ENTREGUE = 'NAO_ENTREGUE', 'Não entregue'

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='essay_submissions',
    )
    course = models.ForeignKey(
        'courses.Disciplina',
        on_delete=models.CASCADE,
        related_name='essay_submissions',
    )
    title = models.CharField(max_length=200)
    prompt = models.TextField(blank=True)
    essay_text = models.TextField(blank=True)
    submission_url = models.URLField(
        blank=True,
        verbose_name='Link da redação',
        help_text='Link externo da redação no Google Docs, Drive ou outra nuvem.',
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUBMITTED,
        verbose_name='Situação',
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    teacher_feedback = models.TextField(blank=True)
    corrected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='essay_corrections',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    corrected_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.title} - {self.student}'

    def clean(self):
        validate_external_resource_url(self.submission_url)

    @property
    def submission_access_url(self):
        return self.submission_url
