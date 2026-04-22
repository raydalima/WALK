from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.utils import OperationalError
from django.db.models import Max

from accounts.models import User
from students.models import Student
from courses.models import Enrollment

from .models import Answer, Choice, Question, Quiz, Submission


def _student_enrolled_course_ids(student):
    return list(
        Enrollment.objects.filter(student=student, is_active=True)
        .values_list('course_id', flat=True)
    )


@login_required
def student_quiz_list(request):
    if getattr(request.user, 'user_type', None) != User.UserType.ALUNO:
        # fallback: permitir listar mesmo assim
        pass

    student = Student.objects.filter(user=request.user).first()
    enrolled_course_ids = _student_enrolled_course_ids(student) if student else []
    selected_course_id = request.GET.get('course')

    try:
        quizzes = (
            Quiz.objects.filter(
                is_published=True,
                course_id__in=enrolled_course_ids,
            )
            .select_related('course')
            .order_by('-created_at')
        )
        if selected_course_id and str(selected_course_id).isdigit():
            quizzes = quizzes.filter(course_id=selected_course_id)

        attempts_by_quiz = {}
        if student and quizzes:
            attempts_by_quiz = {
                item['quiz_id']: item['last_attempt']
                for item in (
                    Submission.objects.filter(student=student, quiz__in=quizzes)
                    .values('quiz_id')
                    .annotate(last_attempt=Max('attempt'))
                )
            }
            for quiz in quizzes:
                quiz.last_attempt = attempts_by_quiz.get(quiz.id)
    except OperationalError:
        quizzes = []
        attempts_by_quiz = {}
        messages.error(
            request,
            'As tabelas de Questionários ainda não foram criadas. '
            'Execute: python3 manage.py migrate',
        )

    return render(
        request,
        'assessments/student_quiz_list.html',
        {
            'quizzes': quizzes,
            'selected_course_id': str(selected_course_id or ''),
        },
    )


@login_required
def student_take_quiz(request, quiz_id):
    try:
        quiz = get_object_or_404(
            Quiz.objects.select_related('course'),
            id=quiz_id,
            is_published=True,
        )
    except OperationalError:
        messages.error(
            request,
            'As tabelas de Questionários ainda não foram criadas. '
            'Execute: python3 manage.py migrate',
        )
        return redirect('assessments:student_quiz_list')

    student = get_object_or_404(Student, user=request.user)

    is_enrolled = Enrollment.objects.filter(
        student=student,
        course_id=quiz.course_id,
        is_active=True,
    ).exists()
    if not is_enrolled:
        messages.error(
            request,
            'Este simulado está disponível apenas para alunos matriculados nesta disciplina.',
        )
        return redirect('assessments:student_quiz_list')

    questions = list(quiz.questions.all().prefetch_related('choices'))

    if request.method == 'POST':
        # múltiplas tentativas: calcular próximo attempt
        last_attempt = (
            Submission.objects.filter(quiz=quiz, student=student)
            .order_by('-attempt')
            .values_list('attempt', flat=True)
            .first()
        )
        attempt = (last_attempt or 0) + 1

        submission = Submission.objects.create(
            quiz=quiz,
            student=student,
            attempt=attempt,
            status=Submission.Status.SUBMITTED,
            submitted_at=timezone.now(),
        )

        for q in questions:
            key = f'q_{q.id}'
            raw = (request.POST.get(key) or '').strip()

            answer = Answer(submission=submission, question=q)

            if q.type in (
                Question.QuestionType.MULTIPLE_CHOICE,
                Question.QuestionType.TRUE_FALSE,
            ):
                if raw.isdigit():
                    answer.selected_choice_id = int(raw)

                # autocorreção
                if answer.selected_choice_id:
                    chosen = (
                        Choice.objects.filter(
                            id=answer.selected_choice_id,
                            question=q,
                        ).first()
                    )
                    if chosen and chosen.is_correct:
                        answer.auto_score = q.points
                    else:
                        answer.auto_score = 0
                else:
                    answer.auto_score = 0

            else:
                answer.text_answer = raw
                # sem auto_score para discursiva

            answer.save()

        messages.success(request, 'Questionário enviado!')
        return redirect('assessments:student_quiz_list')

    return render(
        request,
        'assessments/student_take_quiz.html',
        {
            'quiz': quiz,
            'questions': questions,
        },
    )
