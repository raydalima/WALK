from django.db import models
from students.models import Student


class AreaConhecimento(models.Model):
    NOME_AREAS = [
        ('LINGUAGENS', 'Linguagens, Códigos e suas Tecnologias'),
        ('HUMANAS', 'Ciências Humanas e suas Tecnologias'),
        ('NATUREZA', 'Ciências da Natureza e suas Tecnologias'),
        ('MATEMATICA', 'Matemática e suas Tecnologias'),
        ('REDACAO', 'Redação'),
    ]

    nome = models.CharField(
        max_length=100,
        choices=NOME_AREAS,
        unique=True
    )
    cor_identificacao = models.CharField(max_length=7, default='#007bff')

    class Meta:
        verbose_name = 'Área de Conhecimento'
        verbose_name_plural = 'Áreas de Conhecimento'

    def __str__(self):
        return self.get_nome_display()


class Disciplina(models.Model):
    area = models.ForeignKey(
        AreaConhecimento,
        on_delete=models.CASCADE,
        related_name='disciplinas'
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    icone = models.CharField(max_length=50, blank=True)
    carga_horaria = models.PositiveIntegerField(
        default=0,
        verbose_name='Carga Horária',
    )
    conteudo_programatico = models.TextField(
        blank=True,
        verbose_name='Conteúdo Programático',
    )
    teachers = models.ManyToManyField(
        'teachers.Teacher',
        blank=True,
        related_name='courses',
        verbose_name='Professores',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativa')

    class Meta:
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'

    def __str__(self):
        try:
            return (
                f"{self.nome} "
                f"({self.area.get_nome_display()})"
            )
        except Exception:
            return self.nome

    @property
    def name(self):
        return self.nome

    @property
    def description(self):
        return self.descricao

    @property
    def code(self):
        if self.pk:
            return f"DISC-{self.pk:03d}"
        return "DISC-NOVA"

    @property
    def teacher(self):
        return self.teachers.first()

    @property
    def workload(self):
        return self.carga_horaria

    @property
    def semester(self):
        return None

    @property
    def year(self):
        return None

    @property
    def enrolled_students_count(self):
        try:
            return self.enrollments.filter(is_active=True).count()
        except Exception:
            return 0


class Turma(models.Model):
    class Shift(models.TextChoices):
        MANHA = 'MANHA', 'Manhã'
        TARDE = 'TARDE', 'Tarde'
        NOITE = 'NOITE', 'Noite'
        INTEGRAL = 'INTEGRAL', 'Integral'

    class Status(models.TextChoices):
        PLANEJADA = 'PLANEJADA', 'Planejada'
        EM_ANDAMENTO = 'EM_ANDAMENTO', 'Em andamento'
        ENCERRADA = 'ENCERRADA', 'Encerrada'
        INATIVA = 'INATIVA', 'Inativa'

    nome = models.CharField(max_length=120, verbose_name='Nome da Turma')
    ano = models.PositiveIntegerField(verbose_name='Ano')
    turno = models.CharField(
        max_length=20,
        choices=Shift.choices,
        default=Shift.NOITE,
        verbose_name='Turno',
    )
    descricao = models.TextField(blank=True, verbose_name='Descrição')
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EM_ANDAMENTO,
        verbose_name='Situação',
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    disciplines = models.ManyToManyField(
        Disciplina,
        blank=True,
        related_name='turmas',
        verbose_name='Disciplinas',
    )
    teachers = models.ManyToManyField(
        'teachers.Teacher',
        blank=True,
        related_name='turmas',
        verbose_name='Professores',
    )
    students = models.ManyToManyField(
        Student,
        through='TurmaEnrollment',
        blank=True,
        related_name='turmas',
        verbose_name='Alunos',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Turma'
        verbose_name_plural = 'Turmas'
        ordering = ['-ano', 'nome']
        unique_together = [('nome', 'ano')]

    def __str__(self):
        return f'{self.nome} ({self.ano})'

    @property
    def active_students_count(self):
        return self.class_enrollments.filter(is_active=True).count()


class TurmaEnrollment(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='class_enrollments',
        verbose_name='Aluno',
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='class_enrollments',
        verbose_name='Turma',
    )
    joined_at = models.DateField(auto_now_add=True, verbose_name='Ingresso')
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    notes = models.TextField(blank=True, verbose_name='Observações')

    class Meta:
        verbose_name = 'Matrícula em Turma'
        verbose_name_plural = 'Matrículas em Turmas'
        unique_together = [('student', 'turma')]
        ordering = ['-joined_at']

    def __str__(self):
        return f'{self.student} - {self.turma}'


# Compatibilidade:
# se o código antigo referir 'Course', mapeamos para Disciplina
Course = Disciplina


# Compatibilidade: alguns módulos/páginas referenciam "Discipline".
# Se o model principal de disciplina do sistema se chama "Course",
# este proxy permite usar "courses.Discipline" em ForeignKeys/strings.
try:
    class Discipline(Course):
        class Meta:
            proxy = True
            verbose_name = 'Disciplina'
            verbose_name_plural = 'Disciplinas'
except Exception:
    # Se Course não existir por algum motivo durante import, ignorar.
    pass


class Enrollment(models.Model):
    """Modelo para matrículas (relacionamento aluno-disciplina)"""

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Aluno'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
        verbose_name='Disciplina'
    )
    turma = models.ForeignKey(
        Turma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='enrollments',
        verbose_name='Turma',
    )

    enrollment_date = models.DateField(
        auto_now_add=True,
        verbose_name='Data de Matrícula'
    )

    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    notes = models.TextField(blank=True, verbose_name='Observações')

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criado em'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Atualizado em'
    )

    class Meta:
        verbose_name = 'Matrícula'
        verbose_name_plural = 'Matrículas'
        ordering = ['-enrollment_date']
        unique_together = ['student', 'course']

    def __str__(self):
        return (
            f"{self.student.user.get_full_name()} - "
            f"{self.course.nome}"
        )
