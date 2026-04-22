from django.conf import settings
from django.db import models


class AttendanceSession(models.Model):
    turma = models.ForeignKey(
        'courses.Turma',
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        null=True,
        blank=True,
    )
    area = models.ForeignKey(
        'courses.AreaConhecimento',
        on_delete=models.SET_NULL,
        related_name='attendance_sessions',
        null=True,
        blank=True,
    )
    course = models.ForeignKey(
        'courses.Disciplina',
        on_delete=models.CASCADE,
        related_name='attendance_sessions',
        null=True,
        blank=True,
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_sessions_teacher',
    )
    date = models.DateField()
    content_taught = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='attendance_sessions_created',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']
        unique_together = (('turma', 'course', 'date'),)

    def __str__(self):
        reference = self.course or self.area or self.turma
        return f'{reference} - {self.date}'


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'P', 'Presente'
        ABSENT = 'A', 'Ausente'
        JUSTIFIED = 'J', 'Justificado'

    session = models.ForeignKey(
        AttendanceSession,
        on_delete=models.CASCADE,
        related_name='records',
    )
    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    status = models.CharField(
        max_length=1,
        choices=Status.choices,
        default=Status.ABSENT,
        verbose_name='Situação',
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='attendance_records_marked',
    )
    marked_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (('session', 'student'),)
        ordering = ['student_id']

    def __str__(self):
        return (
            f'{self.session} - {self.student} - {self.get_status_display()}'
        )


class ClassDiaryEntry(models.Model):
    turma = models.ForeignKey(
        'courses.Turma',
        on_delete=models.CASCADE,
        related_name='diary_entries',
        verbose_name='Turma',
    )
    area = models.ForeignKey(
        'courses.AreaConhecimento',
        on_delete=models.SET_NULL,
        related_name='diary_entries',
        null=True,
        blank=True,
        verbose_name='Área do Conhecimento',
    )
    course = models.ForeignKey(
        'courses.Disciplina',
        on_delete=models.CASCADE,
        related_name='diary_entries',
        null=True,
        blank=True,
        verbose_name='Disciplina',
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='class_diary_entries',
        verbose_name='Professor Responsável',
    )
    session = models.OneToOneField(
        AttendanceSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='diary_entry',
        verbose_name='Sessão de Frequência',
    )
    date = models.DateField(verbose_name='Data da Aula')
    content = models.TextField(verbose_name='Conteúdo Ministrado')
    notes = models.TextField(blank=True, verbose_name='Observações')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')

    class Meta:
        verbose_name = 'Diário de Turma'
        verbose_name_plural = 'Diários de Turma'
        ordering = ['-date', '-id']

    def __str__(self):
        reference = self.course or self.area or self.turma
        return f'{self.turma} - {reference} - {self.date}'
