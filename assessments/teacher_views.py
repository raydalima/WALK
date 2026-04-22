from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.db.utils import OperationalError

from accounts.decorators import teacher_required

from .models import Choice, Question, Quiz, Submission


@login_required
@teacher_required
def quiz_list(request):
    """Lista questionários do professor.

    Se as migrations ainda não foram aplicadas, evita erro 500.
    """
    try:
        quizzes = (
            Quiz.objects.filter(created_by=request.user)
            .select_related('course')
        )
    except OperationalError:
        quizzes = []
        messages.error(
            request,
            'Migrations do app "assessments" não aplicadas (tabelas não existem). '
            'Rode: python3 manage.py migrate',
        )

    return render(
        request,
        'assessments/teacher/quiz_list.html',
        {'quizzes': quizzes},
    )


@login_required
@teacher_required
def quiz_create(request):
    try:
        return _quiz_create_impl(request)
    except OperationalError:
        messages.error(
            request,
            'As tabelas de Questionários ainda não foram criadas. '
            'Execute: python3 manage.py migrate',
        )
        return redirect('teachers:assessments_teacher:quiz_list')


def _quiz_create_impl(request):
    from django import forms
    from courses.models import Disciplina

    class QuizForm(forms.ModelForm):
        class Meta:
            model = Quiz
            fields = ['course', 'title', 'description', 'due_date']

    teacher = getattr(request.user, 'teacher_profile', None)

    def _course_queryset():
        base_qs = Disciplina.objects.filter(is_active=True).order_by('nome')
        if teacher is None:
            return base_qs
        teacher_qs = base_qs.filter(teachers=teacher)
        return teacher_qs if teacher_qs.exists() else base_qs

    if request.method == 'POST':
        form = QuizForm(request.POST)
        form.fields['course'].queryset = _course_queryset()
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, 'Questionário criado. Agora adicione perguntas.')
            return redirect('teachers:assessments_teacher:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizForm()
        form.fields['course'].queryset = _course_queryset()

    return render(request, 'assessments/teacher/quiz_create.html', {'form': form})


@login_required
@teacher_required
def quiz_detail(request, quiz_id):
    try:
        quiz = get_object_or_404(
            Quiz.objects.select_related('course'),
            id=quiz_id,
        )
        questions = list(quiz.questions.all())
    except OperationalError:
        messages.error(
            request,
            'As tabelas de Questionários ainda não foram criadas. '
            'Execute: python3 manage.py migrate',
        )
        return redirect('teachers:assessments_teacher:quiz_list')

    return render(
        request,
        'assessments/teacher/quiz_detail.html',
        {
            'quiz': quiz,
            'questions': questions,
        },
    )


@login_required
@teacher_required
def quiz_publish(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)
    if quiz.questions.count() == 0:
        messages.error(request, 'Adicione pelo menos 1 pergunta antes de publicar.')
        return redirect('teachers:assessments_teacher:quiz_detail', quiz_id=quiz.id)

    quiz.is_published = True
    quiz.save()
    messages.success(request, 'Questionário publicado!')
    return redirect('teachers:assessments_teacher:quiz_detail', quiz_id=quiz.id)


@login_required
@teacher_required
def question_create(request, quiz_id):
    from django import forms

    quiz = get_object_or_404(Quiz, id=quiz_id, created_by=request.user)

    class QuestionForm(forms.ModelForm):
        class Meta:
            model = Question
            fields = ['text', 'type', 'order', 'points', 'correct_text']
            widgets = {
                'text': forms.Textarea(
                    attrs={
                        'class': 'form-control',
                        'rows': 4,
                        'placeholder': 'Digite o enunciado da pergunta.',
                    }
                ),
                'type': forms.Select(attrs={'class': 'form-select'}),
                'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
                'points': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
                'correct_text': forms.Textarea(
                    attrs={
                        'class': 'form-control',
                        'rows': 3,
                        'placeholder': 'Preencha apenas para resposta curta ou discursiva, quando quiser deixar um gabarito de referência.',
                    }
                ),
            }

        labels = {
            'text': 'Enunciado',
            'type': 'Tipo da pergunta',
            'order': 'Ordem',
            'points': 'Pontuação',
            'correct_text': 'Gabarito textual',
        }

    class ChoiceForm(forms.Form):
        text = forms.CharField(
            max_length=300,
            required=False,
            widget=forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Texto da alternativa',
                }
            ),
        )
        is_correct = forms.BooleanField(
            required=False,
            widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        )

    ChoiceFormSet = formset_factory(ChoiceForm, extra=4, min_num=0, validate_min=False)

    if request.method == 'POST':
        q_form = QuestionForm(request.POST)
        c_formset = ChoiceFormSet(request.POST, prefix='c')
        if q_form.is_valid() and c_formset.is_valid():
            q = q_form.save(commit=False)
            q.quiz = quiz
            q.save()

            if q.type in (Question.QuestionType.MULTIPLE_CHOICE, Question.QuestionType.TRUE_FALSE):
                for f in c_formset:
                    text = (f.cleaned_data.get('text') or '').strip()
                    if not text:
                        continue
                    Choice.objects.create(
                        question=q,
                        text=text,
                        is_correct=bool(f.cleaned_data.get('is_correct')),
                    )

            messages.success(request, 'Pergunta adicionada!')
            return redirect('teachers:assessments_teacher:quiz_detail', quiz_id=quiz.id)
    else:
        q_form = QuestionForm(initial={'order': quiz.questions.count() + 1, 'points': 1})
        c_formset = ChoiceFormSet(prefix='c')

    return render(
        request,
        'assessments/teacher/question_create.html',
        {'quiz': quiz, 'q_form': q_form, 'c_formset': c_formset},
    )


@login_required
@teacher_required
def submission_list(request, quiz_id):
    try:
        quiz = get_object_or_404(Quiz, id=quiz_id)
        submissions = (
            Submission.objects.filter(quiz=quiz)
            .select_related('student__user')
            .order_by('-id')
        )
    except OperationalError:
        messages.error(
            request,
            'As tabelas de Questionários ainda não foram criadas. '
            'Execute: python3 manage.py migrate',
        )
        return redirect('teachers:assessments_teacher:quiz_list')

    return render(
        request,
        'assessments/teacher/submission_list.html',
        {
            'quiz': quiz,
            'submissions': submissions,
        },
    )


@login_required
@teacher_required
def grade_submission(request, submission_id):
    try:
        return _grade_submission_impl(request, submission_id)
    except OperationalError:
        messages.error(
            request,
            'As tabelas de Questionários ainda não foram criadas. '
            'Execute: python3 manage.py migrate',
        )
        return redirect('teachers:assessments_teacher:quiz_list')


def _grade_submission_impl(request, submission_id):
    from django import forms

    sub = get_object_or_404(
        Submission.objects.select_related(
            'quiz',
            'student__user',
            'quiz__course',
        ),
        id=submission_id,
    )

    if sub.quiz.created_by_id != request.user.id:
        messages.error(request, 'Acesso negado.')
        return redirect('teachers:assessments_teacher:quiz_list')

    answers = list(sub.answers.select_related('question', 'selected_choice').all())

    class GradeForm(forms.Form):
        pass

    for a in answers:
        if a.question.type in (
            Question.QuestionType.MULTIPLE_CHOICE,
            Question.QuestionType.TRUE_FALSE,
        ):
            choices = [('', '---------')] + [
                (choice.id, choice.text)
                for choice in a.question.choices.all()
            ]
            GradeForm.base_fields[f'answer_choice_{a.id}'] = forms.ChoiceField(
                required=False,
                choices=choices,
                initial=a.selected_choice_id or '',
                label='Resposta do aluno',
                widget=forms.Select(attrs={'class': 'form-select'}),
            )
        else:
            GradeForm.base_fields[f'answer_text_{a.id}'] = forms.CharField(
                required=False,
                initial=a.text_answer,
                label='Resposta do aluno',
                widget=forms.Textarea(
                    attrs={
                        'rows': 5,
                        'class': 'form-control',
                    }
                ),
            )
        GradeForm.base_fields[f'score_{a.id}'] = forms.DecimalField(
            required=False,
            max_digits=6,
            decimal_places=2,
            initial=a.teacher_score,
            label='Nota',
            widget=forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'step': '0.5',
                    'min': '0',
                }
            ),
        )
        GradeForm.base_fields[f'fb_{a.id}'] = forms.CharField(
            required=False,
            widget=forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'form-control',
                }
            ),
            initial=a.teacher_feedback,
            label='Feedback',
        )

    if request.method == 'POST':
        form = GradeForm(request.POST)
        if form.is_valid():
            for a in answers:
                if a.question.type in (
                    Question.QuestionType.MULTIPLE_CHOICE,
                    Question.QuestionType.TRUE_FALSE,
                ):
                    selected_choice_id = form.cleaned_data.get(f'answer_choice_{a.id}')
                    a.selected_choice_id = int(selected_choice_id) if selected_choice_id else None
                    a.text_answer = ''
                    if a.selected_choice_id:
                        selected = a.question.choices.filter(id=a.selected_choice_id).first()
                        a.auto_score = a.question.points if selected and selected.is_correct else 0
                    else:
                        a.auto_score = 0
                else:
                    a.text_answer = form.cleaned_data.get(f'answer_text_{a.id}', '')
                    a.selected_choice = None
                a.teacher_score = form.cleaned_data.get(f'score_{a.id}')
                a.teacher_feedback = form.cleaned_data.get(f'fb_{a.id}', '')
                a.save()

            sub.status = Submission.Status.GRADED
            sub.corrected_at = timezone.now()
            sub.corrected_by = request.user
            sub.save()

            messages.success(request, 'Envio corrigido!')
            return redirect(
                'teachers:assessments_teacher:submission_list',
                quiz_id=sub.quiz_id,
            )
    else:
        form = GradeForm()

    return render(
        request,
        'assessments/teacher/grade_submission.html',
        {
            'submission': sub,
            'answers': answers,
            'form': form,
        },
    )
