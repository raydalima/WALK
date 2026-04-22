import csv
from io import BytesIO

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.forms import formset_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from accounts.decorators import teacher_required
from courses.models import Course, Enrollment, Turma
from materials.models import Material, VideoLesson
from assessments.forms import EssayCorrectionForm, TeacherActivityCorrectionForm
from assessments.models import Activity, ActivityResult, EssaySubmission
from students.models import Student

from .forms import MaterialForm, VideoLessonForm
from .models import Teacher


def _teacher_profile(user):
    return Teacher.objects.get_or_create(user=user)[0]


def _teacher_courses():
    return Course.objects.select_related('area').prefetch_related('teachers').order_by('nome')


def _course_enrollments(course):
    return (
        Enrollment.objects.filter(course=course, is_active=True)
        .select_related('student__user')
        .order_by('student__user__first_name', 'student__user__last_name')
    )


def _pdf_escape_text(value):
    text = (
        str(value or '')
        .replace('\\', '\\\\')
        .replace('(', '\\(')
        .replace(')', '\\)')
    )
    return text.encode('cp1252', errors='replace').decode('latin-1')


def _build_simple_pdf(lines, title):
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
            "/F1 10 Tf",
            f"1 0 0 1 {left_margin} {page_height - top_margin} Tm",
            f"({_pdf_escape_text(title)}) Tj",
        ]
        y_offset = line_height * 2
        for line in page_lines:
            content_lines.append(
                f"1 0 0 1 {left_margin} {page_height - top_margin - y_offset} Tm"
            )
            content_lines.append(f"({_pdf_escape_text(line)}) Tj")
            y_offset += line_height
        content_lines.append("ET")
        content_stream = "\n".join(content_lines).encode("latin-1")
        content_obj = add_object(
            b"<< /Length " + str(len(content_stream)).encode() + b" >>\nstream\n"
            + content_stream + b"\nendstream"
        )
        content_ids.append(content_obj)
        page_ids.append(add_object(b""))

    pages_obj = add_object(b"")
    for index, page_obj in enumerate(page_ids):
        page_dict = (
            f"<< /Type /Page /Parent {pages_obj} 0 R /MediaBox [0 0 {page_width} {page_height}] "
            f"/Resources << /Font << /F1 {font_obj} 0 R >> >> /Contents {content_ids[index]} 0 R >>"
        ).encode()
        objects[page_obj - 1] = page_dict

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_obj - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    ).encode()

    catalog_obj = add_object(f"<< /Type /Catalog /Pages {pages_obj} 0 R >>".encode())

    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for object_id, obj in enumerate(objects, start=1):
        offsets.append(buffer.tell())
        buffer.write(f"{object_id} 0 obj\n".encode())
        buffer.write(obj)
        buffer.write(b"\nendobj\n")

    xref_offset = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode())
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode())

    buffer.write(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_obj} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF"
        ).encode()
    )
    return buffer.getvalue()


class AttendanceLineForm(forms.Form):
    student_id = forms.IntegerField(widget=forms.HiddenInput)
    name = forms.CharField(required=False, disabled=True)
    status = forms.ChoiceField(
        choices=[('P', 'Presente'), ('A', 'Ausente'), ('J', 'Justificado')],
        widget=forms.Select,
    )


@login_required
@teacher_required
def dashboard(request):
    teacher = _teacher_profile(request.user)
    courses_qs = _teacher_courses().filter(teachers=teacher)
    if not courses_qs.exists():
        courses_qs = _teacher_courses()
    courses = list(courses_qs[:8])
    recent_materials = (
        Material.objects.filter(uploaded_by=request.user, is_active=True)
        .select_related('course')[:5]
    )
    recent_videos = (
        VideoLesson.objects.filter(uploaded_by=request.user, is_active=True)
        .select_related('course')[:5]
    )
    essays_qs = (
        EssaySubmission.objects.filter(course__in=courses_qs)
        .select_related('student__user', 'course')
    )
    activities_qs = _teacher_activity_queryset(request.user, teacher)
    pending_essays_count = essays_qs.exclude(
        status=EssaySubmission.Status.CORRECTED
    ).count()
    pending_activity_results_count = ActivityResult.objects.filter(
        activity__in=activities_qs,
        status__in=[
            ActivityResult.Status.ENVIADA,
            ActivityResult.Status.EM_CORRECAO,
            ActivityResult.Status.REVISAO_SOLICITADA,
        ],
    ).count()

    return render(
        request,
        'teachers/dashboard.html',
        {
            'teacher': teacher,
            'courses': courses,
            'recent_materials': recent_materials,
            'recent_videos': recent_videos,
            'courses_count': courses_qs.count(),
            'recent_materials_count': recent_materials.count(),
            'recent_videos_count': recent_videos.count(),
            'pending_essays_count': pending_essays_count,
            'activities_count': activities_qs.count(),
            'pending_activity_results_count': pending_activity_results_count,
        },
    )


@login_required
@teacher_required
def my_courses(request):
    teacher = _teacher_profile(request.user)
    courses_qs = _teacher_courses().filter(teachers=teacher)
    if not courses_qs.exists():
        courses_qs = _teacher_courses()
    courses = list(courses_qs)
    return render(
        request,
        'teachers/my_courses.html',
        {'teacher': teacher, 'courses': courses},
    )


@login_required
@teacher_required
def course_materials(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    materials = (
        Material.objects.filter(course=course, is_active=True)
        .select_related('uploaded_by')
        .order_by('-upload_date')
    )
    return render(
        request,
        'teachers/course_materials.html',
        {'course': course, 'materials': materials},
    )


@login_required
@teacher_required
def upload_material(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = MaterialForm(request.POST, course=course)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.area = getattr(course, 'area', None)
            material.uploaded_by = request.user
            material.full_clean()
            material.save()
            messages.success(request, 'Material cadastrado por link com sucesso!')
            return redirect('teachers:course_materials', course_id=course.id)
    else:
        form = MaterialForm(course=course)

    return render(
        request,
        'teachers/upload_material.html',
        {'course': course, 'form': form},
    )


@login_required
@teacher_required
def delete_material(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    course_id = material.course_id
    material.is_active = False
    material.save(update_fields=['is_active'])
    messages.success(request, 'Material removido com sucesso!')
    return redirect('teachers:course_materials', course_id=course_id)


@login_required
@teacher_required
def course_videos(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    video_lessons = (
        VideoLesson.objects.filter(course=course, is_active=True)
        .order_by('lesson_number', 'title')
    )
    return render(
        request,
        'teachers/course_videos.html',
        {'course': course, 'video_lessons': video_lessons},
    )


@login_required
@teacher_required
def add_video(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = VideoLessonForm(request.POST)
        if form.is_valid():
            video = form.save(commit=False)
            video.course = course
            video.uploaded_by = request.user
            video.save()
            messages.success(request, 'Aula em vídeo adicionada com sucesso!')
            return redirect('teachers:course_videos', course_id=course.id)
    else:
        form = VideoLessonForm()

    return render(
        request,
        'teachers/add_video.html',
        {'course': course, 'form': form},
    )


@login_required
@teacher_required
def delete_video(request, video_id):
    video = get_object_or_404(VideoLesson, id=video_id)
    course_id = video.course_id
    video.is_active = False
    video.save(update_fields=['is_active'])
    messages.success(request, 'Aula em vídeo removida com sucesso!')
    return redirect('teachers:course_videos', course_id=course_id)


@login_required
@teacher_required
def course_students(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = list(_course_enrollments(course))
    students = [enrollment.student for enrollment in enrollments]

    return render(
        request,
        'teachers/course_students.html',
        {
            'course': course,
            'enrollments': enrollments,
            'students': students,
        },
    )


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def course_attendance(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = list(_course_enrollments(course))

    if request.method == 'POST':
        marked_ids = set(request.POST.getlist('present'))
        total = len(enrollments)
        present = sum(
            1 for enrollment in enrollments if str(enrollment.student_id) in marked_ids
        )
        messages.success(
            request,
            f'Frequência registrada nesta sessão: {present}/{total} presentes.',
        )
        return redirect('teachers:course_attendance', course_id=course.id)

    return render(
        request,
        'teachers/course_attendance.html',
        {'course': course, 'enrollments': enrollments},
    )


@login_required
@teacher_required
def course_attendance_csv(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollments = _course_enrollments(course)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="frequencia_{course.id}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(['Aluno', 'E-mail', 'Presente (marcar)'])
    for enrollment in enrollments:
        user = enrollment.student.user
        writer.writerow([user.get_full_name() or user.username, user.email, ''])

    return response


@login_required
@teacher_required
def student_diagnostic(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    enrollments = (
        Enrollment.objects.filter(student=student, is_active=True)
        .select_related('course')
        .order_by('course__nome')
    )
    courses = [enrollment.course for enrollment in enrollments]

    return render(
        request,
        'teachers/student_diagnostic.html',
        {
            'student': student,
            'enrollments': enrollments,
            'courses': courses,
        },
    )


@login_required
@teacher_required
@require_http_methods(["GET", "POST"])
def student_feedback(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    if request.method == 'POST':
        feedback = (request.POST.get('feedback') or '').strip()
        if feedback:
            messages.success(request, 'Feedback enviado nesta sessão.')
        else:
            messages.error(request, 'Escreva um feedback antes de enviar.')
        return redirect('teachers:student_feedback', student_id=student.id)

    return render(
        request,
        'teachers/student_feedback.html',
        {'student': student},
    )


@login_required
@teacher_required
def corrections_home(request):
    teacher = _teacher_profile(request.user)
    courses_qs = _teacher_courses().filter(teachers=teacher)
    if not courses_qs.exists():
        courses_qs = _teacher_courses()

    essays = (
        EssaySubmission.objects.filter(course__in=courses_qs)
        .select_related('student__user', 'course', 'corrected_by')
        .order_by('-submitted_at')
    )

    pending_essays = essays.exclude(status=EssaySubmission.Status.CORRECTED)[:8]
    corrected_essays = essays.filter(status=EssaySubmission.Status.CORRECTED)[:8]

    return render(
        request,
        'teachers/corrections_home.html',
        {
            'pending_essays': pending_essays,
            'corrected_essays': corrected_essays,
        },
    )


def _teacher_activity_queryset(user, teacher):
    return (
        Activity.objects.filter(
            Q(teacher=user) |
            Q(turma__teachers=teacher) |
            Q(course__teachers=teacher)
        )
        .select_related('turma', 'area', 'course', 'teacher')
        .distinct()
        .order_by('-created_at')
    )


@login_required
@teacher_required
def activity_submissions_list(request):
    teacher = _teacher_profile(request.user)
    activities = _teacher_activity_queryset(request.user, teacher)
    status_filter = request.GET.get('status', '')

    activity_rows = []
    for activity in activities:
        students_count = activity.turma.class_enrollments.filter(is_active=True).count()
        results = activity.results.all()
        if status_filter:
            results = results.filter(status=status_filter)
        activity_rows.append(
            {
                'activity': activity,
                'students_count': students_count,
                'submitted_count': results.filter(
                    status__in=[
                        ActivityResult.Status.ENVIADA,
                        ActivityResult.Status.EM_CORRECAO,
                        ActivityResult.Status.CORRIGIDA,
                        ActivityResult.Status.REVISAO_SOLICITADA,
                        ActivityResult.Status.ENTREGUE,
                    ]
                ).count(),
                'corrected_count': results.filter(
                    status=ActivityResult.Status.CORRIGIDA
                ).count(),
                'pending_count': max(
                    students_count
                    - activity.results.exclude(
                        status__in=[
                            ActivityResult.Status.PENDENTE,
                            ActivityResult.Status.NAO_ENTREGUE,
                            ActivityResult.Status.NAO_FEZ,
                            ActivityResult.Status.AUSENTE,
                        ]
                    ).count(),
                    0,
                ),
            }
        )

    return render(
        request,
        'teachers/activities_list.html',
        {
            'activity_rows': activity_rows,
            'status_filter': status_filter,
            'status_choices': ActivityResult.Status.choices,
        },
    )


@login_required
@teacher_required
def activity_submissions_detail(request, activity_id):
    teacher = _teacher_profile(request.user)
    activity = get_object_or_404(
        _teacher_activity_queryset(request.user, teacher),
        id=activity_id,
    )
    status_filter = request.GET.get('status', '')
    students = (
        Student.objects.filter(
            class_enrollments__turma=activity.turma,
            class_enrollments__is_active=True,
        )
        .select_related('user')
        .distinct()
        .order_by('user__first_name', 'user__last_name')
    )
    existing = {
        result.student_id: result
        for result in activity.results.select_related('student__user', 'corrected_by')
    }

    rows = []
    for student in students:
        result = existing.get(student.id)
        current_status = (
            result.status if result else ActivityResult.Status.PENDENTE
        )
        if status_filter and current_status != status_filter:
            continue
        rows.append(
            {
                'student': student,
                'result': result,
                'status': current_status,
                'status_label': dict(ActivityResult.Status.choices).get(current_status, current_status),
            }
        )

    return render(
        request,
        'teachers/activity_detail.html',
        {
            'activity': activity,
            'rows': rows,
            'status_filter': status_filter,
            'status_choices': ActivityResult.Status.choices,
        },
    )


@login_required
@teacher_required
def activity_result_update(request, activity_id, student_id):
    teacher = _teacher_profile(request.user)
    activity = get_object_or_404(
        _teacher_activity_queryset(request.user, teacher),
        id=activity_id,
    )
    student = get_object_or_404(
        Student.objects.select_related('user'),
        id=student_id,
        class_enrollments__turma=activity.turma,
        class_enrollments__is_active=True,
    )
    result, _ = ActivityResult.objects.get_or_create(
        activity=activity,
        student=student,
        defaults={'status': ActivityResult.Status.PENDENTE},
    )

    if request.method == 'POST':
        form = TeacherActivityCorrectionForm(request.POST, instance=result)
        if form.is_valid():
            result = form.save(commit=False)
            result.corrected_by = request.user
            if result.status == ActivityResult.Status.CORRIGIDA:
                result.corrected_at = timezone.now()
            result.save()
            messages.success(request, 'Correção da atividade atualizada com sucesso.')
            return redirect('teachers:activity_submissions_detail', activity_id=activity.id)
    else:
        if result.status == ActivityResult.Status.ENVIADA:
            result.status = ActivityResult.Status.EM_CORRECAO
            result.save(update_fields=['status', 'updated_at'])
        form = TeacherActivityCorrectionForm(instance=result)

    return render(
        request,
        'teachers/activity_result_detail.html',
        {
            'activity': activity,
            'student': student,
            'result': result,
            'form': form,
        },
    )


@login_required
@teacher_required
def essay_correction_detail(request, essay_id):
    teacher = _teacher_profile(request.user)
    courses_qs = _teacher_courses().filter(teachers=teacher)
    if not courses_qs.exists():
        courses_qs = _teacher_courses()
    essay = get_object_or_404(
        EssaySubmission.objects.select_related('student__user', 'course', 'corrected_by'),
        id=essay_id,
        course__in=courses_qs,
    )

    if request.method == 'POST':
        form = EssayCorrectionForm(request.POST, instance=essay)
        if form.is_valid():
            essay = form.save(commit=False)
            essay.corrected_by = request.user
            if essay.status == EssaySubmission.Status.CORRECTED:
                essay.corrected_at = timezone.now()
            essay.save()
            messages.success(request, 'Correção da redação salva com sucesso.')
            return redirect('teachers:corrections_home')
    else:
        if essay.status == EssaySubmission.Status.SUBMITTED:
            essay.status = EssaySubmission.Status.UNDER_REVIEW
            essay.save(update_fields=['status'])
        form = EssayCorrectionForm(instance=essay)

    return render(
        request,
        'teachers/essay_correction_detail.html',
        {
            'essay': essay,
            'form': form,
        },
    )


@login_required
@teacher_required
def attendance_home(request):
    teacher = _teacher_profile(request.user)
    courses = _teacher_courses().filter(teachers=teacher)
    if not courses.exists():
        courses = _teacher_courses()
    turmas = Turma.objects.filter(teachers=teacher).distinct().order_by('-ano', 'nome')
    if not turmas.exists():
        turmas = Turma.objects.filter(is_active=True).order_by('-ano', 'nome')
    return render(
        request,
        'teachers/attendance/home.html',
        {'courses': courses, 'turmas': turmas},
    )


@login_required
@teacher_required
def attendance_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    Session = apps.get_model('attendance', 'AttendanceSession')
    sessions = Session.objects.filter(course_id=course.id).order_by('-date', '-id')

    return render(
        request,
        'teachers/attendance/course.html',
        {'course': course, 'sessions': sessions},
    )


@login_required
@teacher_required
def attendance_session_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    Session = apps.get_model('attendance', 'AttendanceSession')
    enrollments = list(_course_enrollments(course))
    turmas_qs = Turma.objects.filter(
        disciplines=course,
        is_active=True,
    ).order_by('-ano', 'nome').distinct()
    if not turmas_qs.exists():
        turmas_qs = Turma.objects.filter(
            enrollments__course=course,
            is_active=True,
        ).order_by('-ano', 'nome').distinct()

    class SessionForm(forms.ModelForm):
        class Meta:
            model = Session
            fields = ['turma', 'date', 'content_taught', 'notes']
            widgets = {
                'turma': forms.Select(attrs={'class': 'form-select'}),
                'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
                'content_taught': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ex.: Função afim, interpretação de gráficos, resolução comentada.'}),
                'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações gerais da aula, atrasos, avisos ou ocorrências.'}),
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['turma'].required = False
            self.fields['turma'].queryset = turmas_qs
            self.fields['turma'].empty_label = 'Sem turma específica'
            self.fields['date'].label = 'Data da aula'
            self.fields['content_taught'].label = 'Conteúdo ministrado'
            self.fields['notes'].label = 'Observações da aula'

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.course = course
            session.teacher = request.user
            session.created_by = request.user
            session.save()
            messages.success(request, 'Sessão de frequência criada.')
            return redirect(
                'teachers:attendance_session_detail',
                session_id=session.id,
            )
    else:
        form = SessionForm(
            initial={
                'date': timezone.localdate(),
                'turma': turmas_qs.first().id if turmas_qs.count() == 1 else None,
            }
        )

    return render(
        request,
        'teachers/attendance/session_create.html',
        {
            'course': course,
            'form': form,
            'student_count': len(enrollments),
            'turmas': list(turmas_qs[:6]),
        },
    )


@login_required
@teacher_required
def attendance_session_detail(request, session_id):
    Session = apps.get_model('attendance', 'AttendanceSession')
    Record = apps.get_model('attendance', 'AttendanceRecord')

    session = get_object_or_404(Session, id=session_id)
    enrollments = list(_course_enrollments(session.course))
    LineFormSet = formset_factory(AttendanceLineForm, extra=0)
    existing = {
        record.student_id: record
        for record in Record.objects.filter(session=session)
    }

    initial = []
    counts = {'P': 0, 'A': 0, 'J': 0}
    for enrollment in enrollments:
        student = enrollment.student
        user = student.user
        record = existing.get(student.id)
        current_status = getattr(record, 'status', 'A')
        counts[current_status] = counts.get(current_status, 0) + 1
        initial.append(
            {
                'student_id': student.id,
                'name': user.get_full_name() or user.username,
                'status': current_status,
            }
        )

    if request.method == 'POST':
        formset = LineFormSet(request.POST)
        if formset.is_valid():
            with transaction.atomic():
                for form in formset:
                    student_id = form.cleaned_data['student_id']
                    status = form.cleaned_data['status']
                    record = existing.get(student_id)
                    if record is None:
                        record = Record(session=session, student_id=student_id)
                    record.status = status
                    record.marked_by = request.user
                    record.save()
            messages.success(request, 'Frequência salva.')
            return redirect(
                'teachers:attendance_session_detail',
                session_id=session.id,
            )
    else:
        formset = LineFormSet(initial=initial)

    return render(
        request,
        'teachers/attendance/session_detail.html',
        {
            'session': session,
            'formset': formset,
            'total_students': len(enrollments),
            'present_count': counts.get('P', 0),
            'absent_count': counts.get('A', 0),
            'justified_count': counts.get('J', 0),
        },
    )


@login_required
@teacher_required
def attendance_session_csv(request, session_id):
    Session = apps.get_model('attendance', 'AttendanceSession')
    Record = apps.get_model('attendance', 'AttendanceRecord')

    session = get_object_or_404(Session, id=session_id)
    records = (
        Record.objects.filter(session=session)
        .select_related('student__user')
        .order_by('student__user__first_name', 'student__user__last_name')
    )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        f'attachment; filename="frequencia_{session.course_id}_{session.date}.csv"'
    )

    writer = csv.writer(response)
    writer.writerow(['Aluno', 'Situação', 'Data', 'Disciplina'])
    for record in records:
        user = record.student.user
        writer.writerow(
            [
                user.get_full_name() or user.username,
                record.get_status_display(),
                session.date,
                session.course.nome,
            ]
        )

    return response


@login_required
@teacher_required
def attendance_session_pdf(request, session_id):
    Session = apps.get_model('attendance', 'AttendanceSession')
    Record = apps.get_model('attendance', 'AttendanceRecord')

    session = get_object_or_404(Session, id=session_id)
    records = (
        Record.objects.filter(session=session)
        .select_related('student__user')
        .order_by('student__user__first_name', 'student__user__last_name')
    )

    lines = [
        f"Disciplina: {session.course.nome if session.course else '-'}",
        f"Data: {session.date}",
        f"Turma: {session.turma if session.turma else 'Sem turma especifica'}",
        f"Conteudo: {session.content_taught or '-'}",
        "-" * 110,
        "Aluno | Situação",
        "-" * 110,
    ]

    for record in records:
        user = record.student.user
        student_name = user.get_full_name() or user.username
        lines.append(
            f"{student_name[:70]:70} | {record.get_status_display()}"
        )

    pdf = _build_simple_pdf(
        lines,
        title=f"Frequencia - {session.course.nome if session.course else 'Sessao'}",
    )

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="frequencia_{session.course_id}_{session.date}.pdf"'
    )
    return response


@login_required
@teacher_required
def materials_list(request):
    courses = list(_teacher_courses())
    materials_by_course = [
        (
            course,
            Material.objects.filter(course=course, is_active=True).order_by('-upload_date')[:50],
        )
        for course in courses
    ]
    total_materials = sum(len(materials) for _, materials in materials_by_course)
    courses_with_materials = sum(1 for _, materials in materials_by_course if materials)

    return render(
        request,
        'teachers/materials_list.html',
        {
            'courses': courses,
            'materials_by_course': materials_by_course,
            'material_model_found': True,
            'total_materials': total_materials,
            'courses_with_materials': courses_with_materials,
        },
    )
