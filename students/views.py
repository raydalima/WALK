from django.shortcuts import (
    render,
    get_object_or_404,
    redirect,
)
from django.contrib.auth.decorators import login_required
from accounts.decorators import student_required
from .models import Student, PreRegistration
from django.apps import apps
from materials.models import Material, VideoLesson
from assessments.forms import StudentActivitySubmissionForm, StudentEssaySubmissionForm
from assessments.models import Activity, ActivityResult, EssaySubmission
from django.db import OperationalError
from django.db.models import Q
from django.http import HttpResponse
from .forms import PreRegistrationForm
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
import logging
import os


try:
    Course = apps.get_model('courses', 'Disciplina')
except LookupError:
    Course = None

try:
    Enrollment = apps.get_model('courses', 'Enrollment')
except LookupError:
    Enrollment = None


# configurar logger local para erros de pré-cadastro
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
logger = logging.getLogger('pre_registration')
if not logger.handlers:
    fh = logging.FileHandler(os.path.join(log_dir, 'pre_registration_errors.log'))
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    logger.setLevel(logging.ERROR)


@login_required
@student_required
def dashboard(request):
    """Dashboard do aluno"""
    student_courses = []
    recent_posts = []
    recent_materials = []
    recent_videos = []
    recent_quizzes = []
    recent_essays = []
    recent_activities = []

    Post = apps.get_model('blog', 'BlogPost')
    Quiz = apps.get_model('assessments', 'Quiz')

    student = None
    if Student:
        try:
            student = Student.objects.filter(user=request.user).first()
        except Exception:
            try:
                user_email = getattr(request.user, 'email', None)
                student = Student.objects.filter(
                    email=user_email
                ).first()
            except Exception:
                student = None

    if student is not None and Enrollment is not None:
        try:
            enrolls = (
                Enrollment.objects.filter(student=student, is_active=True)
                .select_related('course')
            )
            student_courses = [e.course for e in enrolls if getattr(e, 'course', None)]
            course_ids = [course.id for course in student_courses if getattr(course, 'id', None)]
        except Exception:
            student_courses = []
            course_ids = []
    else:
        course_ids = []

    if Post:
        try:
            recent_posts = list(Post.objects.all().order_by('-id')[:5])
        except Exception:
            recent_posts = []

    if course_ids:
        try:
            turma_ids = _student_active_turma_ids(student)
            recent_materials = list(
                Material.objects.filter(course_id__in=course_ids, is_active=True)
                .filter(Q(turma__isnull=True) | Q(turma_id__in=turma_ids))
                .select_related('course', 'uploaded_by')
                .order_by('-upload_date')[:5]
            )
        except Exception:
            recent_materials = []

        try:
            recent_videos = list(
                VideoLesson.objects.filter(course_id__in=course_ids, is_active=True)
                .select_related('course', 'uploaded_by')
                .order_by('-created_at', 'lesson_number')[:5]
            )
        except Exception:
            recent_videos = []

        if Quiz:
            try:
                recent_quizzes = list(
                    Quiz.objects.filter(course_id__in=course_ids, is_published=True)
                    .select_related('course')
                    .order_by('-created_at')[:5]
                )
            except Exception:
                recent_quizzes = []

        try:
            recent_essays = list(
                EssaySubmission.objects.filter(student=student)
                .select_related('course')
                .order_by('-submitted_at')[:5]
            )
        except Exception:
            recent_essays = []

    if student is not None:
        try:
            turma_ids = _student_active_turma_ids(student)
            recent_activities = list(
                Activity.objects.filter(turma_id__in=turma_ids)
                .select_related('turma', 'course', 'area')
                .order_by('-created_at')[:5]
            )
        except Exception:
            recent_activities = []

    context = {
        'student_courses': student_courses,
        'student_courses_count': len(student_courses),
        'recent_posts': recent_posts,
        'recent_posts_count': len(recent_posts),
        'recent_materials': recent_materials,
        'recent_materials_count': len(recent_materials),
        'recent_videos': recent_videos,
        'recent_videos_count': len(recent_videos),
        'recent_quizzes': recent_quizzes,
        'recent_quizzes_count': len(recent_quizzes),
        'recent_essays': recent_essays,
        'recent_essays_count': len(recent_essays),
        'recent_activities': recent_activities,
        'recent_activities_count': len(recent_activities),
    }

    return render(request, 'students/dashboard.html', context)


@login_required
@student_required
def my_courses(request):
    """Lista de disciplinas matriculadas"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    try:
        enrollments = (
            Enrollment.objects.filter(
                student=student,
                is_active=True,
            ).select_related('course')
        )
    except OperationalError:
        enrollments = []

    context = {
        'student': student,
        'enrollments': enrollments,
    }
    return render(request, 'students/my_courses.html', context)


@login_required
@student_required
def course_detail(request, course_id):
    """Detalhes de uma disciplina"""
    if Course is None:
        return render(request, 'students/course_detail.html', {'course': None, 'enrollment': None, 'materials': [], 'video_lessons': [], 'error': 'Modelo de Curso não encontrado.'})
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    course = get_object_or_404(Course, id=course_id)

    enrollment = Enrollment.objects.filter(
        student=student,
        course=course,
        is_active=True,
    ).first()

    turma_ids = _student_active_turma_ids(student)
    try:
        materials = (
            Material.objects.filter(course=course, is_active=True)
            .filter(Q(turma__isnull=True) | Q(turma_id__in=turma_ids))
            .order_by('-upload_date')
        )

        video_lessons = (
            VideoLesson.objects.filter(course=course, is_active=True)
            .order_by('lesson_number')
        )
    except OperationalError:
        materials = []
        video_lessons = []

    quizzes = []
    try:
        Quiz = apps.get_model('assessments', 'Quiz')
        quizzes = (
            Quiz.objects.filter(course=course, is_published=True)
            .order_by('-created_at')
        )
    except Exception:
        quizzes = []

    context = {
        'course': course,
        'enrollment': enrollment,
        'materials': materials,
        'video_lessons': video_lessons,
        'quizzes': quizzes,
    }
    return render(request, 'students/course_detail.html', context)


@login_required
@student_required
def materials_list(request, course_id=None):
    """
    Lista todos os materiais das disciplinas matriculadas ou de uma
    disciplina específica.
    """
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    # Se for solicitada uma disciplina específica,
    # verificar matrícula e filtrar
    if course_id is not None:
        if Course is None:
            return render(request, 'students/materials_list.html', {'materials': [], 'error': 'Modelo de Curso não encontrado.'})
        course = get_object_or_404(Course, id=course_id)
        enrolled = (
            Enrollment.objects.filter(
                student=student,
                course=course,
                is_active=True,
            ).exists()
        )
        if not enrolled:
            materials = []
        else:
            turma_ids = _student_active_turma_ids(student)
            try:
                materials = (
                    Material.objects.filter(
                        course=course,
                        is_active=True,
                    )
                    .filter(Q(turma__isnull=True) | Q(turma_id__in=turma_ids))
                    .select_related('course', 'uploaded_by')
                    .order_by('-upload_date')
                )
            except OperationalError:
                materials = []
    else:
        # Buscar cursos matriculados
        if Course is None:
            return render(request, 'students/materials_list.html', {'materials': [], 'error': 'Modelo de Curso não encontrado.'})
        enrolled_courses = Course.objects.filter(
            enrollments__student=student,
            enrollments__is_active=True,
        )

        # Materiais dos cursos matriculados
        turma_ids = _student_active_turma_ids(student)
        try:
            materials = (
                Material.objects.filter(
                    course__in=enrolled_courses,
                    is_active=True,
                )
                .filter(Q(turma__isnull=True) | Q(turma_id__in=turma_ids))
                .select_related('course', 'uploaded_by')
                .order_by('-upload_date')
            )
        except OperationalError:
            materials = []

    context = {
        'materials': materials,
    }
    return render(request, 'students/materials_list.html', context)


@login_required
@student_required
def video_lessons_list(request):
    """Lista todas as aulas em vídeo das disciplinas matriculadas"""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    # Buscar cursos matriculados
    if Course is None:
        return render(request, 'students/video_lessons_list.html', {'video_lessons': [], 'error': 'Modelo de Curso não encontrado.'})
    enrolled_courses = Course.objects.filter(
        enrollments__student=student,
        enrollments__is_active=True,
    )

    lessons = (
        VideoLesson.objects.filter(
            course__in=enrolled_courses,
            is_active=True,
        )
        .select_related('course')
        .order_by('course__nome', 'lesson_number')
    )

    context = {
        'video_lessons': lessons,
    }
    return render(request, 'students/video_lessons_list.html', context)


def course_list(request):
    """Lista cursos disponíveis com links para exportar matrícula (DOC/PDF)."""
    if Course is None:
        return HttpResponse(
            'Modelo de disciplina não encontrado no app courses',
            status=500,
        )

    courses = Course.objects.select_related('area').all().order_by('nome')
    return render(
        request,
        'students/course_list.html',
        {'courses': courses},
    )


@login_required
@student_required
def profile(request):
    """Exibe os dados cadastrais do aluno (apenas leitura)."""
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    context = {
        'student': student,
        'user': request.user,
    }
    return render(request, 'students/profile.html', context)


def pre_registration(request):
    """Mantém compatibilidade com a rota antiga de pré-cadastro."""
    return pre_cadastro(request)


@require_POST
def pre_registration_submit(request):
    form = PreRegistrationForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(
            request,
            (
                'Pré-matrícula enviada com sucesso. '
                'Em breve entraremos em contato.'
            ),
        )
        return redirect('/#pre-matricula')

    # Re-renderiza a home com o form preenchido e erros
    messages.error(
        request,
        'Não foi possível enviar sua pré-matrícula. Confira os campos.',
    )
    return render(
        request,
        'home.html',
        {
            'pre_registration_form': form,
        },
        status=400,
    )


def thanks(request):
    """Página de agradecimento após pré-matrícula."""
    return render(request, 'students/thanks.html')


def materials(request):
    # obter modelo dinamicamente e proteger caso não exista
    Material = None
    try:
        Material = apps.get_model('materials', 'Material')
    except LookupError:
        Material = None

    materials = Material.objects.all() if Material is not None else []
    return render(
        request,
        'students/materiais.html',
        {'materials': materials},
    )


@login_required
@student_required
def essay_list(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    essays = (
        EssaySubmission.objects.filter(student=student)
        .select_related('course', 'corrected_by')
        .order_by('-submitted_at')
    )
    return render(
        request,
        'students/essay_list.html',
        {'essays': essays},
    )


@login_required
@student_required
def essay_submit(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    enrolled_courses = Course.objects.filter(
        enrollments__student=student,
        enrollments__is_active=True,
    ).order_by('nome')

    if request.method == 'POST':
        form = StudentEssaySubmissionForm(
            request.POST,
            course_queryset=enrolled_courses,
        )
        if form.is_valid():
            essay = form.save(commit=False)
            essay.student = student
            essay.status = EssaySubmission.Status.SUBMITTED
            essay.save()
            messages.success(request, 'Redação enviada para correção com sucesso.')
            return redirect('students:essay_list')
    else:
        form = StudentEssaySubmissionForm(course_queryset=enrolled_courses)

    return render(
        request,
        'students/essay_submit.html',
        {'form': form},
    )


def _student_active_turma_ids(student):
    """Retorna turmas ativas do aluno usando as matrículas disponíveis."""
    turma_ids = set(
        student.class_enrollments.filter(is_active=True)
        .values_list('turma_id', flat=True)
    )
    if Enrollment is not None:
        turma_ids.update(
            Enrollment.objects.filter(
                student=student,
                is_active=True,
                turma__isnull=False,
            ).values_list('turma_id', flat=True)
        )
    return list(turma_ids)


@login_required
@student_required
def activity_list(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    activities = (
        Activity.objects.filter(turma_id__in=_student_active_turma_ids(student))
        .select_related('turma', 'area', 'course', 'teacher')
        .order_by('-created_at')
    )
    course_id = request.GET.get('course')
    if course_id:
        activities = activities.filter(course_id=course_id)

    activities = list(activities)
    results = {
        result.activity_id: result
        for result in ActivityResult.objects.filter(
            student=student,
            activity__in=activities,
        )
    }
    status_filter = request.GET.get('status', '')
    if status_filter:
        activities = [
            activity
            for activity in activities
            if (
                results.get(activity.id).status
                if results.get(activity.id)
                else ActivityResult.Status.PENDENTE
            ) == status_filter
        ]

    return render(
        request,
        'students/activity_list.html',
        {
            'activities': activities,
            'results': results,
            'status_filter': status_filter,
            'status_choices': ActivityResult.Status.choices,
        },
    )


@login_required
@student_required
def activity_submit(request, activity_id):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        student = Student.objects.create(user=request.user)

    activity = get_object_or_404(
        Activity.objects.select_related('turma', 'area', 'course'),
        id=activity_id,
        turma_id__in=_student_active_turma_ids(student),
    )
    result, _ = ActivityResult.objects.get_or_create(
        activity=activity,
        student=student,
        defaults={'status': ActivityResult.Status.PENDENTE},
    )

    if request.method == 'POST':
        form = StudentActivitySubmissionForm(request.POST, instance=result)
        if form.is_valid():
            result = form.save(commit=False)
            result.activity = activity
            result.student = student
            result.status = ActivityResult.Status.ENVIADA
            result.submitted_at = timezone.now()
            result.save()
            messages.success(request, 'Atividade enviada com sucesso.')
            return redirect('students:activity_list')
    else:
        form = StudentActivitySubmissionForm(instance=result)

    return render(
        request,
        'students/activity_submit.html',
        {
            'activity': activity,
            'result': result,
            'form': form,
        },
    )


def _apply_bootstrap_classes_to_form(form):
    """Aplica classes Bootstrap básicas aos widgets do formulário para renderização sem widget_tweaks."""
    for name, field in form.fields.items():
        widget = field.widget
        classes = widget.attrs.get('class', '')
        if 'form-check-input' in classes or isinstance(widget.attrs.get('type'), str) and widget.attrs.get('type') == 'checkbox':
            # manter classes de checkbox
            widget.attrs['class'] = (classes + ' form-check-input').strip()
        else:
            widget.attrs['class'] = (classes + ' form-control').strip()


def pre_cadastro(request):
    """Formulário de pré-cadastro com tratamento de erros para evitar 500 no POST."""
    if request.method == 'POST':
        form = PreRegistrationForm(request.POST)
        try:
            _apply_bootstrap_classes_to_form(form)
        except Exception:
            pass

        if form.is_valid():
            try:
                preregistration = form.save()
                try:
                    subject = 'Confirmação de pré-cadastro - WALK'
                    message = (
                        f'Olá {preregistration.name},\n\n'
                        'Recebemos seu pré-cadastro com sucesso. '
                        'A equipe administrativa analisará suas informações '
                        'e poderá usar esses dados no processo de matrícula.\n\n'
                        'Atenciosamente,\nEquipe WALK'
                    )
                    from_email = getattr(
                        settings,
                        'DEFAULT_FROM_EMAIL',
                        'contato@walk.com',
                    )
                    send_mail(
                        subject,
                        message,
                        from_email,
                        [preregistration.email],
                        fail_silently=True,
                    )
                except Exception:
                    pass
                messages.success(
                    request,
                    'Pré-cadastro enviado com sucesso. A equipe administrativa utilizará esses dados para análise e matrícula.',
                )
                return redirect('students:thanks')
            except Exception as exc:  # captura erros inesperados ao salvar
                import traceback

                tb = traceback.format_exc()
                logger.error('Erro ao salvar pré-cadastro: %s', tb)
                traceback.print_exc()
                messages.error(
                    request,
                    'Ocorreu um erro ao salvar sua pré-matrícula. Tente novamente mais tarde.',
                )
        else:
            messages.error(
                request,
                'Não foi possível enviar sua pré-matrícula. Verifique os campos e tente novamente.',
            )
    else:
        form = PreRegistrationForm()
        try:
            _apply_bootstrap_classes_to_form(form)
        except Exception:
            pass

    return render(request, 'students/pre_cadastro.html', {'form': form})
