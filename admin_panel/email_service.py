from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMessage
from django.db.models import Q
from django.utils import timezone

from assessments.models import ActivityResult
from attendance.models import AttendanceRecord
from courses.models import Turma
from students.models import Student
from teachers.models import Teacher

from .models import EmailCommunication, EmailCommunicationRecipient


@dataclass(frozen=True)
class EmailTarget:
    email: str
    name: str
    recipient_type: str
    student: Student | None = None
    teacher: Teacher | None = None


def _student_name(student):
    return student.user.get_full_name() or student.user.username or student.user.email


def _teacher_name(teacher):
    return teacher.user.get_full_name() or teacher.user.username or teacher.user.email


def _student_email_target(student):
    return EmailTarget(
        email=(student.user.email or '').strip(),
        name=_student_name(student),
        recipient_type=EmailCommunicationRecipient.RecipientType.ALUNO,
        student=student,
    )


def _responsible_email_target(student):
    return EmailTarget(
        email=(getattr(student, 'responsible_email', '') or '').strip(),
        name=getattr(student, 'responsible_name', '') or f'Responsável de {_student_name(student)}',
        recipient_type=EmailCommunicationRecipient.RecipientType.RESPONSAVEL,
        student=student,
    )


def _teacher_email_target(teacher):
    return EmailTarget(
        email=(teacher.professional_email or teacher.user.email or '').strip(),
        name=_teacher_name(teacher),
        recipient_type=EmailCommunicationRecipient.RecipientType.PROFESSOR,
        teacher=teacher,
    )


def _dedupe_targets(targets):
    seen = set()
    unique = []
    for target in targets:
        key = (target.email.lower(), target.recipient_type, getattr(target.student, 'id', None), getattr(target.teacher, 'id', None))
        if target.email and key not in seen:
            seen.add(key)
            unique.append(target)
    return unique


def students_with_low_frequency(threshold=0.75):
    ids = []
    for student in Student.objects.select_related('user').all():
        records = student.attendance_records.all()
        total = records.count()
        if not total:
            continue
        present = records.filter(status=AttendanceRecord.Status.PRESENT).count()
        if present / total < threshold:
            ids.append(student.id)
    return Student.objects.filter(id__in=ids).select_related('user')


def resolve_email_targets(group, *, student=None, teacher=None, turma=None):
    targets = []

    if group == EmailCommunication.RecipientGroup.ALUNO and student:
        targets.append(_student_email_target(student))
    elif group == EmailCommunication.RecipientGroup.RESPONSAVEL and student:
        targets.append(_responsible_email_target(student))
    elif group == EmailCommunication.RecipientGroup.ALUNO_RESPONSAVEL and student:
        targets.append(_student_email_target(student))
        if student.is_minor or getattr(student, 'responsible_email', ''):
            targets.append(_responsible_email_target(student))
    elif group == EmailCommunication.RecipientGroup.PROFESSOR and teacher:
        targets.append(_teacher_email_target(teacher))
    elif group == EmailCommunication.RecipientGroup.TODOS_ALUNOS:
        targets.extend(_student_email_target(s) for s in Student.objects.select_related('user').filter(is_active=True))
    elif group == EmailCommunication.RecipientGroup.ALUNOS_ATIVOS:
        targets.extend(
            _student_email_target(s)
            for s in Student.objects.select_related('user').filter(
                is_active=True,
                status=Student.Status.CURSANDO,
            )
        )
    elif group == EmailCommunication.RecipientGroup.TODOS_RESPONSAVEIS:
        targets.extend(
            _responsible_email_target(s)
            for s in Student.objects.select_related('user').filter(
                is_active=True,
            ).exclude(responsible_email='')
        )
    elif group == EmailCommunication.RecipientGroup.TODOS_PROFESSORES:
        targets.extend(_teacher_email_target(t) for t in Teacher.objects.select_related('user').filter(is_active=True))
    elif group == EmailCommunication.RecipientGroup.ALUNOS_TURMA and turma:
        targets.extend(
            _student_email_target(enrollment.student)
            for enrollment in turma.class_enrollments.select_related('student__user').filter(is_active=True)
        )
    elif group == EmailCommunication.RecipientGroup.PROFESSORES_TURMA and turma:
        targets.extend(_teacher_email_target(t) for t in turma.teachers.select_related('user').filter(is_active=True))
    elif group == EmailCommunication.RecipientGroup.ALUNOS_BAIXA_FREQUENCIA:
        targets.extend(_student_email_target(s) for s in students_with_low_frequency())
    elif group == EmailCommunication.RecipientGroup.ALUNOS_ATIVIDADE_PENDENTE:
        student_ids = (
            ActivityResult.objects.filter(
                Q(status=ActivityResult.Status.PENDENTE)
                | Q(status=ActivityResult.Status.NAO_ENTREGUE)
                | Q(status=ActivityResult.Status.NAO_FEZ)
            )
            .values_list('student_id', flat=True)
            .distinct()
        )
        targets.extend(_student_email_target(s) for s in Student.objects.select_related('user').filter(id__in=student_ids))

    return _dedupe_targets(targets)


def _create_recipient(communication, target):
    return EmailCommunicationRecipient.objects.create(
        communication=communication,
        email=target.email,
        name=target.name,
        recipient_type=target.recipient_type,
        student=target.student,
        teacher=target.teacher,
    )


def _send_recipient_message(communication, recipient):
    try:
        # Envio individual para não expor destinatários entre si.
        email = EmailMessage(
            subject=communication.subject,
            body=communication.message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient.email],
        )
        email.send(fail_silently=False)
    except Exception as exc:
        recipient.status = EmailCommunicationRecipient.Status.FALHOU
        recipient.error_message = str(exc)
    else:
        recipient.status = EmailCommunicationRecipient.Status.ENVIADO

    recipient.processed_at = timezone.now()
    recipient.save(update_fields=['status', 'processed_at', 'error_message'])
    return recipient


def send_communication_now(communication):
    success = 0
    failed = 0
    last_error = ''

    recipients = communication.recipients.all()
    for recipient in recipients:
        _send_recipient_message(communication, recipient)
        if recipient.status == EmailCommunicationRecipient.Status.ENVIADO:
            success += 1
        else:
            failed += 1
            last_error = recipient.error_message

    communication.successful_recipients = success
    communication.failed_recipients = failed
    communication.sent_at = timezone.now()
    if success and failed:
        communication.status = EmailCommunication.Status.PARCIAL
    elif success:
        communication.status = EmailCommunication.Status.ENVIADO
    else:
        communication.status = EmailCommunication.Status.FALHOU
    communication.error_message = last_error
    communication.save(
        update_fields=[
            'successful_recipients',
            'failed_recipients',
            'sent_at',
            'status',
            'error_message',
        ]
    )
    return communication


def send_due_scheduled_communications():
    due = EmailCommunication.objects.filter(
        status=EmailCommunication.Status.AGENDADO,
        send_immediately=False,
        scheduled_at__lte=timezone.now(),
    ).prefetch_related('recipients')

    sent = []
    for communication in due:
        sent.append(send_communication_now(communication))
    return sent


def create_and_send_communication(
    *,
    subject,
    message,
    send_type,
    recipient_group,
    sent_by,
    targets,
    category='GERAL',
    template=None,
    send_immediately=True,
    scheduled_at=None,
    related_notice=None,
    related_event=None,
):
    communication = EmailCommunication.objects.create(
        subject=subject,
        message=message,
        category=category or 'GERAL',
        template=template,
        send_type=send_type,
        recipient_group=recipient_group,
        sent_by=sent_by,
        total_recipients=len(targets),
        status=(
            EmailCommunication.Status.PENDENTE
            if send_immediately
            else EmailCommunication.Status.AGENDADO
        ),
        send_immediately=send_immediately,
        scheduled_at=scheduled_at,
        related_notice=related_notice,
        related_event=related_event,
    )

    for target in targets:
        _create_recipient(communication, target)

    if not send_immediately:
        return communication

    return send_communication_now(communication)
