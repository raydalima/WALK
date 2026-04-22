from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from .forms import (
    AdminStudentUserForm,
    ActivityForm,
    ActivityResultForm,
    AdministrativeProfileForm,
    AttendanceSessionAdminForm,
    BlogPostForm,
    ClassDiaryEntryForm,
    CalendarEventForm,
    DisciplineAdminForm,
    EmailBulkForm,
    EmailIndividualForm,
    EmailTemplateForm,
    ImportantLinkForm,
    PanelNoticeForm,
    StudentForm,
    TeacherForm,
    DisciplineForm,
    EnrollmentForm,
    StudentAdminForm,
    StudentApprovalForm,
    TurmaEnrollmentForm,
    TurmaForm,
)

from accounts.decorators import admin_required
from accounts.models import User
from accounts.forms import (
    UserRegistrationForm,
    StudentProfileForm,
    TeacherProfileForm,
)
from students.models import PreRegistration, Student, StudentApproval, StudentHistory
from teachers.models import Teacher
from courses.models import Course, Enrollment, Turma, TurmaEnrollment
from blog.models import BlogPost, ImportantLink
from attendance.models import AttendanceRecord, AttendanceSession, ClassDiaryEntry
from assessments.models import Activity, ActivityResult
from admin_panel.email_service import create_and_send_communication, resolve_email_targets
from admin_panel.models import (
    AdministrativeProfile,
    Audience,
    CalendarEvent,
    EmailCommunication,
    EmailTemplate,
    PanelNotice,
)
from django.db.models import Q
from contextlib import suppress
import logging
from django.forms import modelform_factory
from django.http import HttpResponse
import csv
from django.apps import apps
from django.template.loader import render_to_string
from django.utils import timezone
from io import BytesIO
import textwrap
from django.db.models import Count
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

# Alias: usar DisciplineForm como CourseForm quando disponível
CourseForm = DisciplineForm


def _require_admin(user):
    try:
        return (
            user.is_admin_user()
            if hasattr(user, 'is_admin_user')
            else (
                getattr(user, 'is_staff', False)
                or getattr(user, 'is_superuser', False)
            )
        )
    except Exception:
        return (
            getattr(user, 'is_staff', False)
            or getattr(user, 'is_superuser', False)
        )


def _filter_if_field_exists(qs, **kwargs):
    """Aplica filtros somente se os campos existirem no model."""
    try:
        field_names = {f.name for f in qs.model._meta.get_fields()}
    except Exception:
        return qs

    safe_kwargs = {
        k: v for k, v in kwargs.items()
        if k.split('__', 1)[0] in field_names
    }
    return qs.filter(**safe_kwargs) if safe_kwargs else qs


def _build_enrolled_student_rows(search=''):
    enrollments = (
        Enrollment.objects.filter(is_active=True)
        .select_related('student__user', 'course__area')
        .order_by(
            'student__user__first_name',
            'student__user__last_name',
            'student__id',
            'course__nome',
        )
    )

    if search:
        enrollments = enrollments.filter(
            Q(student__user__first_name__icontains=search)
            | Q(student__user__last_name__icontains=search)
            | Q(student__user__email__icontains=search)
            | Q(student__enrollment_number__icontains=search)
            | Q(course__nome__icontains=search)
        )

    rows_by_student = {}
    for enrollment in enrollments:
        student = enrollment.student
        row = rows_by_student.setdefault(
            student.id,
            {
                'student': student,
                'courses': [],
                'course_names': [],
                'course_count': 0,
            },
        )
        row['courses'].append(enrollment.course)
        row['course_names'].append(enrollment.course.nome)

    rows = list(rows_by_student.values())
    for row in rows:
        row['course_count'] = len(row['courses'])
        row['courses_label'] = ', '.join(row['course_names'])
    return rows


def _dashboard_metrics():
    students = Student.objects.all()
    activity_results = ActivityResult.objects.all()
    attendance_records = AttendanceRecord.objects.all()
    return {
        'students_cursando': students.filter(status=Student.Status.CURSANDO, is_active=True).count(),
        'students_aprovados': students.filter(status=Student.Status.APROVADO).count(),
        'students_inativos': students.filter(status=Student.Status.INATIVO).count(),
        'students_evadidos': students.filter(status=Student.Status.EVADIDO).count(),
        'students_low_frequency': len(_students_with_low_frequency_ids()),
        'activity_done': activity_results.filter(
            status__in=[ActivityResult.Status.FEZ, ActivityResult.Status.ENTREGUE]
        ).count(),
        'activity_not_done': activity_results.filter(status=ActivityResult.Status.NAO_FEZ).count(),
        'attendance_absent': attendance_records.filter(status=AttendanceRecord.Status.ABSENT).count(),
        'attendance_present': attendance_records.filter(status=AttendanceRecord.Status.PRESENT).count(),
        'turmas_ativas': Turma.objects.filter(is_active=True).count(),
        'email_communications': EmailCommunication.objects.count(),
        'panel_notices': PanelNotice.objects.count(),
        'calendar_events': CalendarEvent.objects.count(),
    }


def _students_with_low_frequency_ids(threshold=0.75):
    students = (
        Student.objects.annotate(
            total_records=Count('attendance_records'),
            presence_records=Count(
                'attendance_records',
                filter=Q(
                    attendance_records__status__in=[
                        AttendanceRecord.Status.PRESENT,
                        AttendanceRecord.Status.JUSTIFIED,
                    ]
                ),
            ),
        )
        .filter(total_records__gt=0)
    )

    low_frequency_ids = []
    for student in students:
        if (student.presence_records / student.total_records) < threshold:
            low_frequency_ids.append(student.id)
    return low_frequency_ids


def _pdf_escape_text(value):
    text = (value or '').replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    return text.encode('cp1252', errors='replace').decode('latin-1')


def _build_simple_pdf(lines, title='Relacao de Alunos Matriculados'):
    page_width = 842
    page_height = 595
    left_margin = 36
    top_margin = 32
    line_height = 12
    max_lines_per_page = 42

    pages = [lines[i:i + max_lines_per_page] for i in range(0, len(lines), max_lines_per_page)]
    if not pages:
        pages = [[]]

    objects = []

    def add_object(data):
        objects.append(data)
        return len(objects)

    font_obj = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_ids = []
    content_ids = []
    for page_lines in pages:
        content_lines = [
            "BT",
            f"/F1 10 Tf",
            f"1 0 0 1 {left_margin} {page_height - top_margin} Tm",
            f"({ _pdf_escape_text(title) }) Tj",
        ]
        y_offset = line_height * 2
        for line in page_lines:
            content_lines.append(
                f"1 0 0 1 {left_margin} {page_height - top_margin - y_offset} Tm"
            )
            content_lines.append(f"({_pdf_escape_text(line)}) Tj")
            y_offset += line_height
        content_lines.append("ET")
        content_stream = '\n'.join(content_lines).encode('latin-1')
        content_obj = add_object(
            b"<< /Length " + str(len(content_stream)).encode() + b" >>\nstream\n" +
            content_stream + b"\nendstream"
        )
        content_ids.append(content_obj)
        page_ids.append(add_object(b""))

    pages_obj = add_object(b"")
    for idx, page_obj in enumerate(page_ids):
        page_dict = (
            f"<< /Type /Page /Parent {pages_obj} 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_ids[idx]} 0 R >>"
        ).encode()
        objects[page_obj - 1] = page_dict

    kids = ' '.join(f'{page_id} 0 R' for page_id in page_ids)
    objects[pages_obj - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    ).encode()

    catalog_obj = add_object(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>".encode())

    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{index} 0 obj\n".encode())
        buffer.write(obj)
        buffer.write(b"\nendobj\n")

    xref_offset = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode())
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode())
    buffer.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_obj} 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()
    )
    return buffer.getvalue()


def _render_student_report_pdf(request, rows, search=''):
    html_string = render_to_string(
        'admin_panel/relatorio_alunos_geral_pdf.html',
        {
            'rows': rows,
            'search': search,
            'total_alunos': len(rows),
        },
    )

    try:
        from weasyprint import HTML

        return HTML(
            string=html_string,
            base_url=request.build_absolute_uri('/'),
        ).write_pdf()
    except Exception:
        lines = [f"Total de alunos: {len(rows)}"]
        if search:
            lines.append(f"Filtro aplicado: {search}")
        lines.append("")
        lines.append("Aluno | E-mail | Matrícula | CPF | Disciplinas")
        lines.append("-" * 120)

        for row in rows:
            student = row['student']
            base = (
                f"{student.user.get_full_name() or student.user.username} | "
                f"{student.user.email or '-'} | "
                f"{student.enrollment_number or '-'} | "
                f"{student.cpf or '-'} | "
            )
            wrapped_courses = textwrap.wrap(row['courses_label'] or '-', width=40) or ['-']
            lines.append(base + wrapped_courses[0])
            indent = ' ' * len(base)
            for extra_line in wrapped_courses[1:]:
                lines.append(indent + extra_line)
            lines.append("")

        return _build_simple_pdf(lines)


@login_required
def dashboard(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')
    recent_students = Student.objects.all().order_by('-id')[:5]
    recent_activities = Activity.objects.select_related('turma', 'area', 'course')[:5]
    recent_sessions = AttendanceSession.objects.select_related('turma', 'area', 'course')[:5]
    context = {
        'recent_students': recent_students,
        'recent_activities': recent_activities,
        'recent_sessions': recent_sessions,
        'metrics': _dashboard_metrics(),
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
@admin_required
def students_list(request):
    """Lista de alunos"""
    students = Student.objects.all().select_related('user')

    # Busca
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    active = request.GET.get('active', '')
    academic_filter = request.GET.get('academic_filter', '')
    if search:
        students = students.filter(
            Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
            | Q(enrollment_number__icontains=search)
        )
    if status:
        students = students.filter(status=status)
    if active == 'ativos':
        students = students.filter(is_active=True)
    elif active == 'inativos':
        students = students.filter(is_active=False)
    if academic_filter == 'activity_done':
        students = students.filter(
            activity_results__status__in=[
                ActivityResult.Status.FEZ,
                ActivityResult.Status.ENTREGUE,
            ]
        ).distinct()
    elif academic_filter == 'activity_pending':
        students = students.filter(
            activity_results__status__in=[
                ActivityResult.Status.NAO_FEZ,
                ActivityResult.Status.PENDENTE,
            ]
        ).distinct()
    elif academic_filter == 'did_not_attend':
        students = students.filter(
            attendance_records__status=AttendanceRecord.Status.ABSENT
        ).distinct()
    elif academic_filter == 'low_frequency':
        students = students.filter(id__in=_students_with_low_frequency_ids())

    context = {
        'students': students,
        'search': search,
        'status_filter': status,
        'active_filter': active,
        'academic_filter': academic_filter,
        'status_choices': Student.Status.choices,
    }
    return render(request, 'admin_panel/students_list.html', context)


@login_required
@admin_required
def student_create(request):
    """Criar novo aluno"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST, request.FILES)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = User.UserType.ALUNO
            user.save()

            # Criar perfil de aluno
            student = Student.objects.create(user=user)
            StudentHistory.objects.create(
                student=student,
                title='Cadastro inicial',
                description='Aluno cadastrado pelo painel administrativo.',
                created_by=request.user,
            )

            messages.success(
                request,
                f'Aluno {user.get_full_name()} criado com sucesso!'
            )
            return redirect('admin_panel:students_list')
    else:
        user_form = UserRegistrationForm(
            initial={'user_type': User.UserType.ALUNO}
        )

    context = {'form': user_form}
    return render(request, 'admin_panel/student_form.html', context)


@login_required
@admin_required
def student_edit(request, student_id):
    """Editar aluno"""
    student = get_object_or_404(Student, id=student_id)
    approval = student.approvals.order_by('-approval_year', '-id').first()

    if request.method == 'POST':
        user_form = AdminStudentUserForm(request.POST, instance=student.user)
        profile_form = StudentProfileForm(request.POST, instance=student)
        approval_form = StudentApprovalForm(
            request.POST,
            instance=approval,
            prefix='approval',
        )
        if user_form.is_valid() and profile_form.is_valid() and approval_form.is_valid():
            previous_status = student.status
            previous_status_label = student.get_status_display()
            previous_notes = student.notes
            user_form.save()
            updated_student = profile_form.save()
            approval_saved = None
            if not approval_form.is_empty():
                approval_saved = approval_form.save(commit=False)
                approval_saved.student = updated_student
                if approval_saved.created_by_id is None:
                    approval_saved.created_by = request.user
                approval_saved.save()
                if updated_student.status != Student.Status.APROVADO:
                    updated_student.status = Student.Status.APROVADO
                    updated_student.approved_course = approval_saved.course_name
                    updated_student.save(update_fields=['status', 'approved_course'])
            history_messages = []
            if previous_status != updated_student.status:
                history_messages.append(
                    f'Situação alterada de {previous_status_label} para {updated_student.get_status_display()}.'
                )
            if previous_notes != updated_student.notes and updated_student.notes:
                history_messages.append('Observações acadêmicas atualizadas.')
            if approval_saved is not None:
                history_messages.append(
                    f'Aprovação registrada em {approval_saved.institution} para {approval_saved.course_name}.'
                )
            if history_messages:
                StudentHistory.objects.create(
                    student=updated_student,
                    title='Atualização cadastral',
                    description=' '.join(history_messages),
                    created_by=request.user,
                )
            messages.success(
                request,
                'Ficha do aluno atualizada com sucesso!'
            )
            next_url = request.POST.get('next')
            if next_url == 'relatorio':
                return redirect('admin_panel:relatorio_alunos_geral')
            return redirect('admin_panel:students_list')
    else:
        user_form = AdminStudentUserForm(instance=student.user)
        profile_form = StudentProfileForm(instance=student)
        approval_form = StudentApprovalForm(instance=approval, prefix='approval')

    context = {
        'student': student,
        'user_form': user_form,
        'form': profile_form,
        'approval_form': approval_form,
    }
    return render(request, 'admin_panel/student_edit.html', context)


@login_required
@admin_required
def student_delete(request, student_id):
    """Deletar aluno"""
    student = get_object_or_404(Student, id=student_id)
    student.is_active = False
    student.save()
    StudentHistory.objects.create(
        student=student,
        title='Aluno desativado',
        description='Cadastro desativado pelo painel administrativo.',
        created_by=request.user,
    )
    messages.success(request, 'Aluno desativado com sucesso!')
    return redirect('admin_panel:students_list')


# ===== GERÊNCIA DE PROFESSORES =====


@login_required
@admin_required
def teachers_list(request):
    """Lista de professores"""
    teachers = _filter_if_field_exists(
        Teacher.objects.all().select_related('user'),
        is_active=True,
    )

    # Busca
    search = request.GET.get('search', '')
    if search:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__email__icontains=search) |
            Q(specialization__icontains=search)
        )

    context = {
        'teachers': teachers,
        'search': search,
    }
    return render(request, 'admin_panel/teachers_list.html', context)


@login_required
@admin_required
def teacher_create(request):
    """Criar novo professor"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST, request.FILES)
        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = User.UserType.PROFESSOR
            user.save()

            # Criar perfil de professor
            Teacher.objects.create(user=user)

            messages.success(
                request,
                f'Professor {user.get_full_name()} criado com sucesso!'
            )
            return redirect('admin_panel:teachers_list')
    else:
        user_form = UserRegistrationForm(
            initial={'user_type': User.UserType.PROFESSOR}
        )

    context = {'form': user_form}
    return render(request, 'admin_panel/teacher_form.html', context)


@login_required
@admin_required
def teacher_edit(request, teacher_id):
    """Editar professor"""
    teacher = get_object_or_404(Teacher, id=teacher_id)

    if request.method == 'POST':
        profile_form = TeacherProfileForm(request.POST, instance=teacher)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(
                request,
                'Perfil do professor atualizado com sucesso!'
            )
            return redirect('admin_panel:teachers_list')
    else:
        profile_form = TeacherProfileForm(instance=teacher)

    context = {
        'teacher': teacher,
        'form': profile_form,
    }
    return render(request, 'admin_panel/teacher_edit.html', context)


@login_required
@admin_required
def teacher_delete(request, teacher_id):
    """Deletar professor"""
    teacher = get_object_or_404(Teacher, id=teacher_id)
    teacher.is_active = False
    teacher.save()
    messages.success(request, 'Professor desativado com sucesso!')
    return redirect('admin_panel:teachers_list')


# ===== GERÊNCIA DE DISCIPLINAS =====


@login_required
@admin_required
def courses_list(request):
    """Lista de disciplinas"""
    courses = (
        Course.objects.select_related('area').all().order_by('nome')
        if Course is not None else []
    )
    context = {'courses': courses}
    return render(request, 'admin_panel/courses_list.html', context)


@login_required
@admin_required
def course_create(request):
    """Criar nova disciplina"""
    FormClass = DisciplineAdminForm

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Disciplina criada com sucesso!')
            return redirect('admin_panel:courses_list')
    else:
        form = FormClass()

    context = {'form': form}
    return render(request, 'admin_panel/course_form.html', context)


@login_required
@admin_required
def course_edit(request, course_id):
    """Editar disciplina"""
    FormClass = DisciplineAdminForm

    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = FormClass(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Disciplina atualizada com sucesso!')
            return redirect('admin_panel:courses_list')
    else:
        form = FormClass(instance=course)

    context = {
        'course': course,
        'form': form,
    }
    return render(request, 'admin_panel/course_form.html', context)


@login_required
@admin_required
def course_delete(request, course_id):
    """Deletar disciplina"""
    course = get_object_or_404(Course, id=course_id)
    course.is_active = False
    course.save(update_fields=['is_active'])
    messages.success(request, 'Disciplina desativada com sucesso!')
    return redirect('admin_panel:courses_list')


# ===== GERÊNCIA DE TURMAS =====


@login_required
@admin_required
def turmas_list(request):
    turmas = Turma.objects.prefetch_related('disciplines', 'teachers').all()
    search = (request.GET.get('search') or '').strip()
    status = (request.GET.get('status') or '').strip()
    if search:
        turmas = turmas.filter(
            Q(nome__icontains=search)
            | Q(ano__icontains=search)
            | Q(descricao__icontains=search)
        )
    if status:
        turmas = turmas.filter(status=status)
    return render(
        request,
        'admin_panel/turmas_list.html',
        {
            'turmas': turmas.order_by('-ano', 'nome'),
            'search': search,
            'status_filter': status,
            'status_choices': Turma.Status.choices,
        },
    )


@login_required
@admin_required
def turma_create(request):
    if request.method == 'POST':
        form = TurmaForm(request.POST)
        if form.is_valid():
            turma = form.save()
            messages.success(request, f'Turma {turma.nome} criada com sucesso!')
            return redirect('admin_panel:turmas_list')
    else:
        form = TurmaForm()
    return render(request, 'admin_panel/turma_form.html', {'form': form})


@login_required
@admin_required
def turma_edit(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    if request.method == 'POST':
        form = TurmaForm(request.POST, instance=turma)
        if form.is_valid():
            form.save()
            messages.success(request, 'Turma atualizada com sucesso!')
            return redirect('admin_panel:turmas_list')
    else:
        form = TurmaForm(instance=turma)
    return render(
        request,
        'admin_panel/turma_form.html',
        {'form': form, 'turma': turma},
    )


@login_required
@admin_required
def turma_delete(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    turma.is_active = False
    turma.status = Turma.Status.INATIVA
    turma.save(update_fields=['is_active', 'status'])
    messages.success(request, 'Turma desativada com sucesso!')
    return redirect('admin_panel:turmas_list')


@login_required
@admin_required
def turma_students(request, turma_id):
    turma = get_object_or_404(Turma.objects.prefetch_related('class_enrollments__student__user'), id=turma_id)
    enrollments = turma.class_enrollments.select_related('student__user').all()
    return render(
        request,
        'admin_panel/turma_students.html',
        {'turma': turma, 'enrollments': enrollments},
    )


@login_required
@admin_required
def turma_enrollment_create(request):
    if request.method == 'POST':
        form = TurmaEnrollmentForm(request.POST)
        if form.is_valid():
            obj, created = TurmaEnrollment.objects.get_or_create(
                student=form.cleaned_data['student'],
                turma=form.cleaned_data['turma'],
                defaults={
                    'is_active': form.cleaned_data['is_active'],
                    'notes': form.cleaned_data['notes'],
                },
            )
            if not created:
                obj.is_active = form.cleaned_data['is_active']
                obj.notes = form.cleaned_data['notes']
                obj.save()
            messages.success(request, 'Aluno vinculado à turma com sucesso!')
            return redirect('admin_panel:turmas_list')
    else:
        form = TurmaEnrollmentForm()
    return render(request, 'admin_panel/turma_enrollment_form.html', {'form': form})


# ===== FREQUÊNCIA E DIÁRIO =====


@login_required
@admin_required
def attendance_sessions_list(request):
    sessions = AttendanceSession.objects.select_related('turma', 'course', 'teacher').order_by('-date', '-id')
    turma_id = request.GET.get('turma')
    if turma_id:
        sessions = sessions.filter(turma_id=turma_id)
    return render(
        request,
        'admin_panel/attendance_sessions_list.html',
        {'sessions': sessions, 'turmas': Turma.objects.all(), 'turma_id': turma_id or ''},
    )


@login_required
@admin_required
def attendance_session_create(request):
    if request.method == 'POST':
        form = AttendanceSessionAdminForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()
            messages.success(request, 'Sessão de frequência criada com sucesso!')
            return redirect('admin_panel:attendance_sessions_list')
    else:
        form = AttendanceSessionAdminForm(initial={'teacher': request.user.id})
    return render(request, 'admin_panel/attendance_session_form.html', {'form': form})


@login_required
@admin_required
def attendance_session_detail(request, session_id):
    session = get_object_or_404(
        AttendanceSession.objects.select_related('turma', 'course', 'teacher'),
        id=session_id,
    )
    students = []
    if session.turma_id:
        students = Student.objects.filter(
            class_enrollments__turma=session.turma,
            class_enrollments__is_active=True,
        ).select_related('user').distinct()
    elif session.course_id:
        students = Student.objects.filter(
            enrollments__course=session.course,
            enrollments__is_active=True,
        ).select_related('user').distinct()

    existing_records = {
        record.student_id: record
        for record in session.records.select_related('student__user').all()
    }

    if request.method == 'POST':
        has_errors = False
        for student in students:
            status = request.POST.get(f'student_{student.id}')
            if not status:
                continue
            record, _ = AttendanceRecord.objects.get_or_create(
                session=session,
                student=student,
                defaults={'marked_by': request.user},
            )
            record.status = status
            record.marked_by = request.user
            record.save()
        messages.success(request, 'Frequência atualizada com sucesso!')
        return redirect('admin_panel:attendance_session_detail', session_id=session.id)

    return render(
        request,
        'admin_panel/attendance_session_detail.html',
        {
            'session': session,
            'students': students,
            'existing_records': existing_records,
            'status_choices': AttendanceRecord.Status.choices,
        },
    )


@login_required
@admin_required
def diary_entries_list(request):
    entries = ClassDiaryEntry.objects.select_related('turma', 'course', 'teacher').order_by('-date', '-id')
    return render(request, 'admin_panel/diary_entries_list.html', {'entries': entries})


@login_required
@admin_required
def diary_entry_create(request):
    if request.method == 'POST':
        form = ClassDiaryEntryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro de diário criado com sucesso!')
            return redirect('admin_panel:diary_entries_list')
    else:
        form = ClassDiaryEntryForm(initial={'teacher': request.user.id})
    return render(request, 'admin_panel/diary_entry_form.html', {'form': form})


@login_required
@admin_required
def diary_entry_edit(request, entry_id):
    entry = get_object_or_404(ClassDiaryEntry, id=entry_id)
    if request.method == 'POST':
        form = ClassDiaryEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registro de diário atualizado com sucesso!')
            return redirect('admin_panel:diary_entries_list')
    else:
        form = ClassDiaryEntryForm(instance=entry)
    return render(request, 'admin_panel/diary_entry_form.html', {'form': form, 'entry': entry})


# ===== ATIVIDADES =====


@login_required
@admin_required
def activities_list(request):
    status = request.GET.get('status', '')
    activities = Activity.objects.select_related(
        'turma', 'area', 'course', 'teacher', 'created_by'
    ).order_by('-created_at')
    if status:
        activities = activities.filter(status=status)
    return render(
        request,
        'admin_panel/activities_list.html',
        {
            'activities': activities,
            'status_filter': status,
            'status_choices': Activity.Status.choices,
        },
    )


@login_required
@admin_required
def activity_create(request):
    if request.method == 'POST':
        form = ActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.created_by = request.user
            activity.save()
            messages.success(request, 'Atividade criada com sucesso!')
            return redirect('admin_panel:activity_detail', activity_id=activity.id)
    else:
        form = ActivityForm()
    return render(request, 'admin_panel/activity_form.html', {'form': form})


@login_required
@admin_required
def activity_edit(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    if request.method == 'POST':
        form = ActivityForm(request.POST, instance=activity)
        if form.is_valid():
            form.save()
            messages.success(request, 'Atividade atualizada com sucesso!')
            return redirect('admin_panel:activity_detail', activity_id=activity.id)
    else:
        form = ActivityForm(instance=activity)
    return render(request, 'admin_panel/activity_form.html', {'form': form, 'activity': activity})


@login_required
@admin_required
def activity_detail(request, activity_id):
    activity = get_object_or_404(Activity.objects.select_related('turma', 'course'), id=activity_id)
    students = Student.objects.filter(
        class_enrollments__turma=activity.turma,
        class_enrollments__is_active=True,
    ).select_related('user').distinct()
    existing = {result.student_id: result for result in activity.results.all()}

    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.id}', ActivityResult.Status.PENDENTE)
            notes = request.POST.get(f'notes_{student.id}', '')
            submission_url = request.POST.get(f'submission_url_{student.id}', '')
            teacher_feedback = request.POST.get(f'teacher_feedback_{student.id}', '')
            score = request.POST.get(f'score_{student.id}') or None
            result, _ = ActivityResult.objects.get_or_create(
                activity=activity,
                student=student,
            )
            result.status = status
            result.notes = notes
            result.submission_url = submission_url
            result.teacher_feedback = teacher_feedback
            result.score = score
            if submission_url and not result.submitted_at:
                result.submitted_at = timezone.now()
            if status == ActivityResult.Status.CORRIGIDA:
                result.corrected_at = timezone.now()
                result.corrected_by = request.user
            try:
                result.full_clean()
            except ValidationError as exc:
                has_errors = True
                messages.error(
                    request,
                    f'Link inválido para {student.user.get_full_name() or student.user.username}: {exc.messages[0]}',
                )
                continue
            result.save()
        if has_errors:
            return redirect('admin_panel:activity_detail', activity_id=activity.id)
        messages.success(request, 'Situação da atividade atualizada com sucesso!')
        return redirect('admin_panel:activity_detail', activity_id=activity.id)

    return render(
        request,
        'admin_panel/activity_detail.html',
        {
            'activity': activity,
            'students': students,
            'existing': existing,
            'status_choices': ActivityResult.Status.choices,
        },
    )


# ===== ADMINISTRATIVO =====


@login_required
@admin_required
def administrative_list(request):
    admins = AdministrativeProfile.objects.select_related('user').all()
    return render(request, 'admin_panel/administrative_list.html', {'admins': admins})


@login_required
@admin_required
def administrative_create(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST, request.FILES)
        profile_form = AdministrativeProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = User.UserType.ADMIN
            user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            messages.success(request, 'Usuário administrativo criado com sucesso!')
            return redirect('admin_panel:administrative_list')
    else:
        user_form = UserRegistrationForm(initial={'user_type': User.UserType.ADMIN})
        profile_form = AdministrativeProfileForm()
    return render(
        request,
        'admin_panel/administrative_form.html',
        {'user_form': user_form, 'profile_form': profile_form},
    )


# ===== COMUNICAÇÃO POR E-MAIL =====


@login_required
@admin_required
def email_communications_list(request):
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '').strip()
    communications = EmailCommunication.objects.select_related('sent_by').all()
    if search:
        communications = communications.filter(
            Q(subject__icontains=search)
            | Q(message__icontains=search)
            | Q(sent_by__first_name__icontains=search)
            | Q(sent_by__last_name__icontains=search)
        )
    if status:
        communications = communications.filter(status=status)

    return render(
        request,
        'admin_panel/email_communications_list.html',
        {
            'communications': communications,
            'search': search,
            'status': status,
            'status_choices': EmailCommunication.Status.choices,
        },
    )


@login_required
@admin_required
def email_communication_detail(request, communication_id):
    communication = get_object_or_404(
        EmailCommunication.objects.select_related('sent_by'),
        id=communication_id,
    )
    recipients = communication.recipients.select_related(
        'student__user',
        'teacher__user',
    )
    return render(
        request,
        'admin_panel/email_communication_detail.html',
        {
            'communication': communication,
            'recipients': recipients,
        },
    )


def _send_email_form(request, form, send_type):
    targets = resolve_email_targets(
        form.cleaned_data['recipient_group'],
        student=form.cleaned_data.get('student'),
        teacher=form.cleaned_data.get('teacher'),
        turma=form.cleaned_data.get('turma'),
    )
    if not targets:
        messages.error(
            request,
            'Nenhum destinatário com e-mail válido foi encontrado para este envio.',
        )
        return None

    communication = create_and_send_communication(
        subject=form.cleaned_data['subject'],
        message=form.cleaned_data['message'],
        category=form.cleaned_data.get('category') or 'GERAL',
        template=form.cleaned_data.get('template'),
        send_type=send_type,
        recipient_group=form.cleaned_data['recipient_group'],
        sent_by=request.user,
        targets=targets,
        send_immediately=form.cleaned_data.get('send_immediately', True),
        scheduled_at=form.cleaned_data.get('scheduled_at'),
    )
    if communication.status == EmailCommunication.Status.AGENDADO:
        messages.success(
            request,
            f'E-mail agendado para {communication.scheduled_at:%d/%m/%Y %H:%M}.',
        )
        return communication
    if communication.failed_recipients:
        messages.warning(
            request,
            (
                f'Envio processado com {communication.successful_recipients} sucesso(s) '
                f'e {communication.failed_recipients} falha(s).'
            ),
        )
    else:
        messages.success(
            request,
            f'E-mail enviado para {communication.successful_recipients} destinatário(s).',
        )
    return communication


def _recipient_group_from_audience(audience, turma=None):
    if turma:
        if audience == Audience.PROFESSORES:
            return EmailCommunication.RecipientGroup.PROFESSORES_TURMA
        return EmailCommunication.RecipientGroup.ALUNOS_TURMA
    if audience == Audience.PROFESSORES:
        return EmailCommunication.RecipientGroup.TODOS_PROFESSORES
    if audience == Audience.ALUNOS:
        return EmailCommunication.RecipientGroup.TODOS_ALUNOS
    return EmailCommunication.RecipientGroup.TODOS_ALUNOS


def _send_related_email(request, *, subject, message, category, group, turma=None, related_notice=None, related_event=None):
    targets = resolve_email_targets(group, turma=turma)
    if not targets:
        messages.warning(request, 'Aviso/evento salvo, mas nenhum destinatário com e-mail válido foi encontrado.')
        return None

    communication = create_and_send_communication(
        subject=subject,
        message=message,
        category=category,
        send_type=EmailCommunication.SendType.MASSA,
        recipient_group=group,
        sent_by=request.user,
        targets=targets,
        related_notice=related_notice,
        related_event=related_event,
    )
    messages.success(
        request,
        f'E-mail relacionado enviado para {communication.successful_recipients} destinatário(s).',
    )
    return communication


@login_required
@admin_required
def email_individual_create(request):
    if request.method == 'POST':
        form = EmailIndividualForm(request.POST)
        if form.is_valid():
            communication = _send_email_form(
                request,
                form,
                EmailCommunication.SendType.INDIVIDUAL,
            )
            if communication:
                return redirect(
                    'admin_panel:email_communication_detail',
                    communication_id=communication.id,
                )
    else:
        form = EmailIndividualForm()
    return render(
        request,
        'admin_panel/email_individual_form.html',
        {'form': form},
    )


@login_required
@admin_required
def email_bulk_create(request):
    if request.method == 'POST':
        form = EmailBulkForm(request.POST)
        if form.is_valid():
            communication = _send_email_form(
                request,
                form,
                EmailCommunication.SendType.MASSA,
            )
            if communication:
                return redirect(
                    'admin_panel:email_communication_detail',
                    communication_id=communication.id,
                )
    else:
        form = EmailBulkForm()
    return render(
        request,
        'admin_panel/email_bulk_form.html',
        {'form': form},
    )


@login_required
@admin_required
def email_templates_list(request):
    templates = EmailTemplate.objects.select_related('created_by').all()
    return render(
        request,
        'admin_panel/email_templates_list.html',
        {'templates': templates},
    )


@login_required
@admin_required
def email_template_create(request):
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.save()
            messages.success(request, 'Modelo de e-mail criado com sucesso.')
            return redirect('admin_panel:email_templates_list')
    else:
        form = EmailTemplateForm()
    return render(request, 'admin_panel/email_template_form.html', {'form': form})


@login_required
@admin_required
def email_template_edit(request, template_id):
    template = get_object_or_404(EmailTemplate, id=template_id)
    if request.method == 'POST':
        form = EmailTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Modelo de e-mail atualizado com sucesso.')
            return redirect('admin_panel:email_templates_list')
    else:
        form = EmailTemplateForm(instance=template)
    return render(request, 'admin_panel/email_template_form.html', {'form': form, 'template': template})


@login_required
@admin_required
def panel_notices_list(request):
    notices = PanelNotice.objects.select_related('created_by', 'turma').all()
    return render(request, 'admin_panel/panel_notices_list.html', {'notices': notices})


@login_required
@admin_required
def panel_notice_create(request):
    if request.method == 'POST':
        form = PanelNoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.created_by = request.user
            notice.save()
            messages.success(request, 'Aviso publicado no painel/blog.')

            if form.cleaned_data.get('send_email'):
                group = (
                    form.cleaned_data.get('email_recipient_group')
                    or _recipient_group_from_audience(notice.audience, notice.turma)
                )
                _send_related_email(
                    request,
                    subject=notice.title,
                    message=f'{notice.summary}\n\n{notice.content}'.strip(),
                    category=notice.category,
                    group=group,
                    turma=notice.turma,
                    related_notice=notice,
                )
            return redirect('admin_panel:panel_notices_list')
    else:
        form = PanelNoticeForm()
    return render(request, 'admin_panel/panel_notice_form.html', {'form': form})


@login_required
@admin_required
def panel_notice_edit(request, notice_id):
    notice = get_object_or_404(PanelNotice, id=notice_id)
    if request.method == 'POST':
        form = PanelNoticeForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Aviso atualizado com sucesso.')
            return redirect('admin_panel:panel_notices_list')
    else:
        form = PanelNoticeForm(instance=notice)
    return render(request, 'admin_panel/panel_notice_form.html', {'form': form, 'notice': notice})


@login_required
@admin_required
def panel_notice_delete(request, notice_id):
    notice = get_object_or_404(PanelNotice, id=notice_id)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, 'Aviso removido com sucesso.')
        return redirect('admin_panel:panel_notices_list')
    return render(request, 'admin_panel/confirm_delete.html', {'object': notice, 'cancel_url': 'admin_panel:panel_notices_list'})


@login_required
@admin_required
def calendar_events_list(request):
    events = CalendarEvent.objects.select_related('created_by', 'turma', 'related_notice').all()
    return render(request, 'admin_panel/calendar_events_list.html', {'events': events})


@login_required
@admin_required
def calendar_event_create(request):
    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()

            if form.cleaned_data.get('create_notice'):
                notice = PanelNotice.objects.create(
                    title=event.title,
                    summary=f'{event.get_event_type_display()} em {event.starts_at:%d/%m/%Y às %H:%M}',
                    content=event.description or 'Confira a programação institucional do cursinho.',
                    category='EVENTO',
                    audience=event.audience,
                    turma=event.turma,
                    is_featured=event.is_featured,
                    is_visible=event.is_visible,
                    created_by=request.user,
                    published_at=timezone.now(),
                )
                event.related_notice = notice
                event.save(update_fields=['related_notice'])

            messages.success(request, 'Evento cadastrado no calendário institucional.')

            if form.cleaned_data.get('send_email'):
                group = (
                    form.cleaned_data.get('email_recipient_group')
                    or _recipient_group_from_audience(event.audience, event.turma)
                )
                message = (
                    f'{event.title}\n\n'
                    f'Data: {event.starts_at:%d/%m/%Y às %H:%M}\n'
                    f'Local: {event.location or "A definir"}\n\n'
                    f'{event.description}'
                ).strip()
                _send_related_email(
                    request,
                    subject=f'Calendário: {event.title}',
                    message=message,
                    category='EVENTO',
                    group=group,
                    turma=event.turma,
                    related_notice=event.related_notice,
                    related_event=event,
                )
            return redirect('admin_panel:calendar_events_list')
    else:
        form = CalendarEventForm()
    return render(request, 'admin_panel/calendar_event_form.html', {'form': form})


@login_required
@admin_required
def calendar_event_edit(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evento atualizado com sucesso.')
            return redirect('admin_panel:calendar_events_list')
    else:
        form = CalendarEventForm(instance=event)
    return render(request, 'admin_panel/calendar_event_form.html', {'form': form, 'event': event})


@login_required
@admin_required
def calendar_event_delete(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Evento removido do calendário.')
        return redirect('admin_panel:calendar_events_list')
    return render(request, 'admin_panel/confirm_delete.html', {'object': event, 'cancel_url': 'admin_panel:calendar_events_list'})


@login_required
@admin_required
def pre_registrations_list(request):
    search = (request.GET.get('search') or '').strip()
    reviewed = request.GET.get('reviewed', '')

    preregistrations = PreRegistration.objects.all().order_by('-created_at')
    if search:
        preregistrations = preregistrations.filter(
            Q(name__icontains=search)
            | Q(email__icontains=search)
            | Q(phone__icontains=search)
            | Q(intended_course__icontains=search)
        )
    if reviewed == 'sim':
        preregistrations = preregistrations.filter(is_reviewed=True)
    elif reviewed == 'nao':
        preregistrations = preregistrations.filter(is_reviewed=False)

    return render(
        request,
        'admin_panel/pre_registrations_list.html',
        {
            'preregistrations': preregistrations,
            'search': search,
            'reviewed_filter': reviewed,
        },
    )


@login_required
@admin_required
def pre_registration_review(request, preregistration_id):
    preregistration = get_object_or_404(PreRegistration, id=preregistration_id)
    preregistration.is_reviewed = True
    preregistration.reviewed_at = timezone.now()
    preregistration.save(update_fields=['is_reviewed', 'reviewed_at'])
    messages.success(request, 'Pré-cadastro marcado como analisado.')
    return redirect('admin_panel:pre_registrations_list')


# ===== GERÊNCIA DE MATRÍCULAS =====


@login_required
@admin_required
def enrollments_list(request):
    """Lista de matrículas"""
    enrollments = _filter_if_field_exists(
        Enrollment.objects.all().select_related('student__user', 'course'),
        is_active=True,
    )

    context = {'enrollments': enrollments}
    return render(request, 'admin_panel/enrollments_list.html', context)


from django import forms
from django.contrib.auth.decorators import login_required
from accounts.decorators import admin_required


class EnrollmentCreateForm(forms.Form):
    student = forms.ModelChoiceField(
        queryset=Student.objects.select_related('user').all().order_by(
            'user__first_name', 'user__last_name'
        ),
        label='Aluno',
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.select_related('area').all().order_by('nome'),
        label='Disciplina',
    )


@login_required
@admin_required
def enrollment_create(request):
    """Cria uma matrícula manualmente no painel administrativo."""
    if Enrollment is None or Course is None or Student is None:
        messages.error(request, 'Modelos necessários não encontrados.')
        return redirect('admin_panel:enrollments_list')

    if request.method == 'POST':
        form = EnrollmentCreateForm(request.POST)
        if form.is_valid():
            obj, created = Enrollment.objects.get_or_create(
                student=form.cleaned_data['student'],
                course=form.cleaned_data['course'],
                defaults={'is_active': True},
            )
            if not created:
                obj.is_active = True
                obj.save()

            messages.success(request, 'Matrícula criada/atualizada com sucesso.')
            return redirect('admin_panel:enrollments_list')
        messages.error(request, 'Confira os campos e tente novamente.')
    else:
        form = EnrollmentCreateForm()

    return render(
        request,
        'admin_panel/enrollment_form.html',
        {
            'form': form,
        },
    )


@login_required
@admin_required
def enrollment_delete(request, enrollment_id):
    """Deletar matrícula"""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id)
    enrollment.is_active = False
    enrollment.save()
    messages.success(request, 'Matrícula cancelada com sucesso!')
    return redirect('admin_panel:enrollments_list')


# ===== GERÊNCIA DE BLOG =====


@login_required
@admin_required
def blog_posts_list(request):
    """Lista de posts do blog"""
    posts = BlogPost.objects.all().select_related('author')

    context = {'posts': posts}
    return render(request, 'admin_panel/blog_posts_list.html', context)


@login_required
@admin_required
def blog_post_create(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Publicação do blog criada com sucesso!')
            return redirect('admin_panel:blog_posts_list')
    else:
        form = BlogPostForm()

    return render(
        request,
        'admin_panel/blog_post_form.html',
        {'form': form},
    )


@login_required
@admin_required
def blog_post_edit(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)

    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            updated_post = form.save(commit=False)
            if updated_post.author_id is None:
                updated_post.author = request.user
            updated_post.save()
            messages.success(request, 'Publicação do blog atualizada com sucesso!')
            return redirect('admin_panel:blog_posts_list')
    else:
        form = BlogPostForm(instance=post)

    return render(
        request,
        'admin_panel/blog_post_form.html',
        {'form': form, 'post': post},
    )


@login_required
@admin_required
def blog_post_delete(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    post.delete()
    messages.success(request, 'Publicação do blog removida com sucesso!')
    return redirect('admin_panel:blog_posts_list')


@login_required
@admin_required
def important_links_list(request):
    links = ImportantLink.objects.all().select_related('created_by')
    return render(
        request,
        'admin_panel/important_links_list.html',
        {'links': links},
    )


@login_required
@admin_required
def important_link_create(request):
    if request.method == 'POST':
        form = ImportantLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.created_by = request.user
            link.save()
            messages.success(request, 'Link importante criado com sucesso!')
            return redirect('admin_panel:important_links_list')
    else:
        form = ImportantLinkForm()

    return render(
        request,
        'admin_panel/important_link_form.html',
        {'form': form},
    )


@login_required
@admin_required
def important_link_edit(request, link_id):
    link = get_object_or_404(ImportantLink, id=link_id)
    if request.method == 'POST':
        form = ImportantLinkForm(request.POST, instance=link)
        if form.is_valid():
            form.save()
            messages.success(request, 'Link importante atualizado com sucesso!')
            return redirect('admin_panel:important_links_list')
    else:
        form = ImportantLinkForm(instance=link)

    return render(
        request,
        'admin_panel/important_link_form.html',
        {'form': form, 'link': link},
    )


@login_required
@admin_required
def important_link_delete(request, link_id):
    link = get_object_or_404(ImportantLink, id=link_id)
    link.delete()
    messages.success(request, 'Link importante removido com sucesso!')
    return redirect('admin_panel:important_links_list')


@login_required
def alunos_list(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')
    from students.models import Student
    alunos = Student.objects.all()
    return render(
        request,
        'admin_panel/alunos_list.html',
        {'alunos': alunos},
    )


@login_required
def aluno_create(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')

    StudentFormClass = StudentAdminForm or StudentForm
    EnrollmentFormClass = EnrollmentForm

    if request.method == 'POST':
        student_form = (
            StudentFormClass(request.POST)
            if StudentFormClass
            else None
        )
        enrollment_form = (
            EnrollmentFormClass(request.POST)
            if EnrollmentFormClass
            else None
        )

        student_valid = (
            student_form.is_valid() if student_form else True
        )
        enrollment_valid = (
            enrollment_form.is_valid() if enrollment_form else True
        )

        if student_valid and enrollment_valid:
            student_obj = None
            if student_form and hasattr(student_form, 'save'):
                student_obj = student_form.save()

            if enrollment_form and hasattr(enrollment_form, 'save'):
                enrollment_inst = enrollment_form.save(commit=False)
                # tentar vincular student automaticamente
                if student_obj and hasattr(enrollment_inst, 'student'):
                    enrollment_inst.student = student_obj
                with suppress(Exception):
                    enrollment_inst.save()

            messages.success(request, 'Aluno criado com sucesso.')
            return redirect('admin_panel:alunos_list')
    else:
        student_form = (
            StudentFormClass() if StudentFormClass else None
        )
        enrollment_form = (
            EnrollmentFormClass() if EnrollmentFormClass else None
        )

    return render(
        request,
        'admin_panel/aluno_form.html',
        {
            'student_form': student_form,
            'enrollment_form': enrollment_form,
        },
    )


@login_required
def professores_list(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')
    from teachers.models import Teacher
    professores = Teacher.objects.all()
    return render(
        request,
        'admin_panel/professores_list.html',
        {'professores': professores},
    )


@login_required
def professor_create(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')

    FormClass = TeacherForm
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Professor criado com sucesso.')
            return redirect('admin_panel:professores_list')
    else:
        form = FormClass()

    groups = [
        (title, [form[n] for n in names if n in form.fields])
        for title, names in getattr(form, 'field_groups', [])
    ]

    other_fields = [
        form[f]
        for f in getattr(form, 'other_fields', [])
        if f in form.fields
    ]

    return render(
        request,
        'admin_panel/professor_form.html',
        {
            'form': form,
            'groups': groups,
            'other_fields': other_fields,
        },
    )


@login_required
def disciplinas_list(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')
    from courses.models import Discipline
    disciplinas = Discipline.objects.all()
    return render(
        request,
        'admin_panel/disciplinas_list.html',
        {'disciplinas': disciplinas},
    )


@login_required
def disciplina_create(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')
    FormClass = DisciplineForm
    if FormClass is None:
        messages.error(request, 'Formulário de Disciplina indisponível.')
        return redirect('admin_panel:disciplinas_list')
    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Disciplina criada com sucesso.')
            return redirect('admin_panel:disciplinas_list')
    else:
        form = FormClass()
    return render(request, 'admin_panel/disciplina_form.html', {'form': form})


@login_required
def matriculas_list(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')
    from students.models import Enrollment
    matriculas = Enrollment.objects.all()
    return render(
        request,
        'admin_panel/matriculas_list.html',
        {'matriculas': matriculas},
    )


@login_required
def matricula_create(request):
    if not _require_admin(request.user):
        return HttpResponseForbidden('Acesso negado')

    FormClass = EnrollmentForm
    pre_registration_id = request.GET.get('pre_registration')

    if request.method == 'POST':
        form = FormClass(request.POST)
        if form.is_valid():
            try:
                enrollment = form.save()
            except ValidationError as exc:
                form.add_error(None, exc.message)
            else:
                messages.success(request, 'Matrícula criada com sucesso.')
                if getattr(enrollment, 'student_id', None):
                    return redirect(
                        'admin_panel:ficha_aluno',
                        aluno_id=enrollment.student_id,
                    )
                return redirect('admin_panel:matriculas_list')
    else:
        initial = {}
        if pre_registration_id and 'pre_registration' in getattr(FormClass, 'base_fields', {}):
            initial['pre_registration'] = pre_registration_id
        form = FormClass(initial=initial)

    # construir grupos de campos ligados (bound fields)
    groups = [
        (title, [form[n] for n in names if n in form.fields])
        for title, names in getattr(form, 'field_groups', [])
    ]

    other_fields = [
        form[f]
        for f in getattr(form, 'other_fields', [])
        if f in form.fields
    ]

    return render(
        request,
        'admin_panel/matricula_form.html',
        {
            'form': form,
            'groups': groups,
            'other_fields': other_fields,
        },
    )


@login_required
@admin_required
def relatorio_alunos(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = _filter_if_field_exists(
        Enrollment.objects.filter(course=course).select_related('student__user'),
        is_active=True,
    )
    alunos = [e.student for e in enrollments]
    context = {'course': course, 'alunos': alunos}
    return render(
        request,
        'admin_panel/relatorio_alunos.html',
        context,
    )


@login_required
@admin_required
def relatorio_alunos_csv(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = _filter_if_field_exists(
        Enrollment.objects.filter(course=course).select_related('student__user'),
        is_active=True,
    )
    alunos = [e.student for e in enrollments]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="alunos_{course.id}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['Nome', 'E-mail'])
    for aluno in alunos:
        nome_fn = getattr(aluno.user, 'get_full_name', None)
        nome = nome_fn() if callable(nome_fn) else aluno.user.username
        email = getattr(aluno.user, 'email', '')
        writer.writerow([nome, email])
    return response


@login_required
@admin_required
def relatorio_alunos_geral(request):
    search = (request.GET.get('search') or '').strip()
    rows = _build_enrolled_student_rows(search=search)
    return render(
        request,
        'admin_panel/relatorio_alunos_geral.html',
        {
            'rows': rows,
            'search': search,
            'total_alunos': len(rows),
        },
    )


@login_required
@admin_required
def relatorio_alunos_geral_csv(request):
    search = (request.GET.get('search') or '').strip()
    rows = _build_enrolled_student_rows(search=search)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="alunos_geral.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['Nome', 'E-mail', 'Matrícula', 'CPF', 'Disciplinas'])
    for row in rows:
        aluno = row['student']
        nome_fn = getattr(aluno.user, 'get_full_name', None)
        nome = nome_fn() if callable(nome_fn) else aluno.user.username
        writer.writerow([
            nome,
            getattr(aluno.user, 'email', ''),
            aluno.enrollment_number or '',
            aluno.cpf or '',
            row['courses_label'],
        ])
    return response


@login_required
@admin_required
def relatorio_alunos_geral_pdf(request):
    search = (request.GET.get('search') or '').strip()
    rows = _build_enrolled_student_rows(search=search)
    pdf = _render_student_report_pdf(request, rows, search=search)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="relacao_alunos_matriculados.pdf"'
    return response


@login_required
@admin_required
def relatorio_professores_geral(request):
    professores = []
    try:
        TeacherModel = apps.get_model('teachers', 'Teacher')
        professores = TeacherModel.objects.all().select_related('user')
    except Exception:
        professores = []
    return render(
        request,
        'admin_panel/relatorio_professores_geral.html',
        {'professores': professores},
    )


@login_required
@admin_required
def relatorio_professores_geral_csv(request):
    professores = []
    try:
        TeacherModel = apps.get_model('teachers', 'Teacher')
        professores = TeacherModel.objects.all().select_related('user')
    except Exception:
        professores = []

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="professores_geral.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['Nome', 'E-mail'])
    for prof in professores:
        nome_fn = getattr(prof.user, 'get_full_name', None)
        nome = nome_fn() if callable(nome_fn) else prof.user.username
        email = getattr(prof.user, 'email', '')
        writer.writerow([nome, email])
    return response


@login_required
@admin_required
def relatorio_administrativo_geral(request):
    administrativos = AdministrativeProfile.objects.all().select_related('user')
    return render(
        request,
        'admin_panel/relatorio_administrativo_geral.html',
        {'administrativos': administrativos},
    )


@login_required
@admin_required
def relatorio_administrativo_geral_csv(request):
    administrativos = AdministrativeProfile.objects.all().select_related('user')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="administrativo_geral.csv"'
    )
    writer = csv.writer(response)
    writer.writerow(['Nome', 'E-mail'])
    for adm in administrativos:
        nome_fn = getattr(adm.user, 'get_full_name', None)
        nome = nome_fn() if callable(nome_fn) else adm.user.username
        email = getattr(adm.user, 'email', '')
        writer.writerow([nome, email])
    return response


@login_required
@admin_required
def ficha_aluno(request, aluno_id):
    StudentModel = apps.get_model('students', 'Student')
    aluno = get_object_or_404(StudentModel, id=aluno_id)
    enrollments = (
        Enrollment.objects.filter(student=aluno, is_active=True)
        .select_related('course__area')
        .order_by('course__nome')
    )
    return render(
        request,
        'admin_panel/ficha_aluno.html',
        {
            'aluno': aluno,
            'enrollments': enrollments,
            'history_entries': aluno.history_entries.select_related('created_by')[:10],
            'approvals': aluno.approvals.all(),
        },
    )


@login_required
@admin_required
def ficha_professor(request, professor_id):
    TeacherModel = apps.get_model('teachers', 'Teacher')
    professor = get_object_or_404(TeacherModel, id=professor_id)
    return render(
        request,
        'admin_panel/ficha_professor.html',
        {'professor': professor},
    )


@login_required
@admin_required
def relatorio_index(request):
    """Página índice de relatórios (lista cursos/disciplinas quando houver)."""
    courses = Course.objects.all() if Course is not None else []
    turmas = Turma.objects.all().order_by('-ano', 'nome')
    return render(
        request,
        'admin_panel/relatorio_index.html',
        {'courses': courses, 'turmas': turmas},
    )
