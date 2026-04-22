from django import forms
from django.db import transaction
from django.apps import apps
from blog.models import BlogPost, ImportantLink
from contextlib import suppress
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User
from courses.models import Turma, TurmaEnrollment, Disciplina
from attendance.models import AttendanceSession, ClassDiaryEntry
from assessments.models import Activity, ActivityResult
from admin_panel.models import (
    CalendarEvent,
    EmailCommunication,
    EmailTemplate,
    PanelNotice,
    AdministrativeProfile,
)
from students.models import Student, StudentApproval
from teachers.models import Teacher


def get_model_form(app_label, model_name):
    try:
        Model = apps.get_model(app_label, model_name)
    except LookupError:
        Model = None
    if Model is None:
        return None

    class _ModelForm(forms.ModelForm):
        class Meta:
            model = Model
            fields = '__all__'

    return _ModelForm


StudentForm = get_model_form('students', 'Student')
TeacherForm = get_model_form('teachers', 'Teacher')
DisciplineForm = get_model_form('courses', 'Discipline')


# Fallback: se não houver um formulário específico 'Discipline', tentar usar o
# modelo Course como base para um ModelForm dinâmico, permitindo criar/editar
# disciplinas mesmo quando o nome do modelo for diferente.
if DisciplineForm is None:
    for model_name in ('Disciplina', 'Discipline'):
        try:
            CourseModel = apps.get_model('courses', model_name)
            break
        except LookupError:
            CourseModel = None
    if CourseModel is not None:
        class _CourseModelForm(forms.ModelForm):
            class Meta:
                model = CourseModel
                fields = '__all__'

        DisciplineForm = _CourseModelForm


class BlogPostForm(forms.ModelForm):
    """Formulário para posts do blog"""

    class Meta:
        model = BlogPost
        fields = [
            'title',
            'category',
            'content',
            'excerpt',
            'featured_image',
            'is_published',
        ]
        widgets = {
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Título do post',
                }
            ),
            'category': forms.Select(
                attrs={'class': 'form-control'}
            ),
            'content': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 10}
            ),
            'excerpt': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Breve resumo',
                }
            ),
            'featured_image': forms.FileInput(
                attrs={'class': 'form-control'}
            ),
            'is_published': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}
            ),
        }


class ImportantLinkForm(forms.ModelForm):
    class Meta:
        model = ImportantLink
        fields = [
            'title',
            'url',
            'description',
            'category',
            'icon',
            'is_featured',
            'is_active',
            'display_order',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'bi-book'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class AdminStudentUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TurmaForm(forms.ModelForm):
    class Meta:
        model = Turma
        fields = [
            'nome', 'ano', 'turno', 'descricao', 'status', 'is_active',
            'disciplines', 'teachers',
        ]
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'ano': forms.NumberInput(attrs={'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'disciplines': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'teachers': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


class TurmaEnrollmentForm(forms.ModelForm):
    class Meta:
        model = TurmaEnrollment
        fields = ['student', 'turma', 'is_active', 'notes']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DisciplineAdminForm(forms.ModelForm):
    class Meta:
        model = Disciplina
        fields = [
            'area', 'nome', 'descricao', 'icone', 'carga_horaria',
            'conteudo_programatico', 'teachers', 'is_active',
        ]
        widgets = {
            'area': forms.Select(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icone': forms.TextInput(attrs={'class': 'form-control'}),
            'carga_horaria': forms.NumberInput(attrs={'class': 'form-control'}),
            'conteudo_programatico': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'teachers': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AttendanceSessionAdminForm(forms.ModelForm):
    class Meta:
        model = AttendanceSession
        fields = ['turma', 'area', 'course', 'teacher', 'date', 'content_taught', 'notes']
        widgets = {
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'area': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'content_taught': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('area') and cleaned_data.get('course'):
            cleaned_data['area'] = cleaned_data['course'].area
        if not cleaned_data.get('area') and not cleaned_data.get('course'):
            raise forms.ValidationError('Informe ao menos a área ou a disciplina da aula.')
        return cleaned_data


class ClassDiaryEntryForm(forms.ModelForm):
    class Meta:
        model = ClassDiaryEntry
        fields = ['turma', 'area', 'course', 'teacher', 'date', 'content', 'notes']
        widgets = {
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'area': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('area') and cleaned_data.get('course'):
            cleaned_data['area'] = cleaned_data['course'].area
        if not cleaned_data.get('area') and not cleaned_data.get('course'):
            raise forms.ValidationError('Informe ao menos a área ou a disciplina do registro.')
        return cleaned_data


class ActivityForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = ['title', 'description', 'turma', 'area', 'course', 'teacher', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'area': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'teacher': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('area') and cleaned_data.get('course'):
            cleaned_data['area'] = cleaned_data['course'].area
        if not cleaned_data.get('area') and not cleaned_data.get('course'):
            raise forms.ValidationError('Informe ao menos a área ou a disciplina da atividade.')
        return cleaned_data


class ActivityResultForm(forms.ModelForm):
    class Meta:
        model = ActivityResult
        fields = ['student', 'status', 'submission_url', 'notes', 'teacher_feedback', 'score']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'submission_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://docs.google.com/...'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'teacher_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'score': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.5'}),
        }


class AdministrativeProfileForm(forms.ModelForm):
    class Meta:
        model = AdministrativeProfile
        fields = ['role', 'notes', 'is_active']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class StudentApprovalForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = StudentApproval
        fields = ['vestibular', 'institution', 'course_name', 'approval_year', 'notes']
        widgets = {
            'vestibular': forms.TextInput(attrs={'class': 'form-control'}),
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'course_name': forms.TextInput(attrs={'class': 'form-control'}),
            'approval_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def is_empty(self):
        if not hasattr(self, 'cleaned_data'):
            return False
        return not any(self.cleaned_data.get(field) for field in self.fields)

    def clean(self):
        cleaned_data = super().clean()
        if self.is_empty():
            return cleaned_data

        required_fields = ['vestibular', 'institution', 'course_name', 'approval_year']
        for field_name in required_fields:
            if not cleaned_data.get(field_name):
                self.add_error(field_name, 'Preencha este campo para registrar a aprovação.')
        return cleaned_data


class EmailScheduleMixin(forms.Form):
    category = forms.ChoiceField(
        label='Categoria',
        choices=EmailCommunication._meta.get_field('category').choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    template = forms.ModelChoiceField(
        label='Modelo de e-mail',
        queryset=EmailTemplate.objects.filter(is_active=True),
        required=False,
        help_text='Opcional: use um modelo pronto como referência para assunto e mensagem.',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    send_immediately = forms.BooleanField(
        label='Enviar imediatamente',
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    scheduled_at = forms.DateTimeField(
        label='Agendar para',
        required=False,
        help_text='Preencha somente se quiser deixar este envio agendado.',
        widget=forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        send_immediately = cleaned_data.get('send_immediately')
        scheduled_at = cleaned_data.get('scheduled_at')
        cleaned_data['category'] = cleaned_data.get('category') or 'GERAL'
        if not send_immediately and not scheduled_at:
            send_immediately = True
            cleaned_data['send_immediately'] = True

        if not send_immediately:
            if not scheduled_at:
                self.add_error('scheduled_at', 'Informe a data e hora do agendamento.')
            elif scheduled_at <= timezone.now():
                self.add_error('scheduled_at', 'O agendamento precisa ser para uma data futura.')
        return cleaned_data


class EmailIndividualForm(EmailScheduleMixin):
    recipient_group = forms.ChoiceField(
        label='Tipo de destinatário',
        choices=[
            (EmailCommunication.RecipientGroup.ALUNO, 'Aluno'),
            (EmailCommunication.RecipientGroup.PROFESSOR, 'Professor'),
            (EmailCommunication.RecipientGroup.RESPONSAVEL, 'Responsável do aluno'),
            (EmailCommunication.RecipientGroup.ALUNO_RESPONSAVEL, 'Aluno e responsável'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    student = forms.ModelChoiceField(
        label='Aluno',
        queryset=Student.objects.select_related('user').all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    teacher = forms.ModelChoiceField(
        label='Professor',
        queryset=Teacher.objects.select_related('user').filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    subject = forms.CharField(
        label='Assunto',
        max_length=180,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    message = forms.CharField(
        label='Mensagem',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 9,
                'placeholder': 'Escreva o aviso, orientação ou comunicado.',
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get('recipient_group')
        student = cleaned_data.get('student')
        teacher = cleaned_data.get('teacher')

        if group in {
            EmailCommunication.RecipientGroup.ALUNO,
            EmailCommunication.RecipientGroup.RESPONSAVEL,
            EmailCommunication.RecipientGroup.ALUNO_RESPONSAVEL,
        } and not student:
            raise forms.ValidationError('Selecione o aluno para este envio.')

        if group == EmailCommunication.RecipientGroup.PROFESSOR and not teacher:
            raise forms.ValidationError('Selecione o professor para este envio.')

        return cleaned_data


class EmailBulkBaseForm(forms.Form):
    recipient_group = forms.ChoiceField(
        label='Grupo de destinatários',
        choices=[
            (EmailCommunication.RecipientGroup.TODOS_ALUNOS, 'Todos os alunos'),
            (EmailCommunication.RecipientGroup.ALUNOS_ATIVOS, 'Alunos ativos/cursando'),
            (EmailCommunication.RecipientGroup.TODOS_PROFESSORES, 'Todos os professores'),
            (EmailCommunication.RecipientGroup.TODOS_RESPONSAVEIS, 'Todos os responsáveis'),
            (EmailCommunication.RecipientGroup.ALUNOS_TURMA, 'Alunos de uma turma'),
            (EmailCommunication.RecipientGroup.PROFESSORES_TURMA, 'Professores de uma turma'),
            (EmailCommunication.RecipientGroup.ALUNOS_BAIXA_FREQUENCIA, 'Alunos com baixa frequência'),
            (EmailCommunication.RecipientGroup.ALUNOS_ATIVIDADE_PENDENTE, 'Alunos com atividade pendente'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    turma = forms.ModelChoiceField(
        label='Turma',
        queryset=Turma.objects.filter(is_active=True).order_by('-ano', 'nome'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    subject = forms.CharField(
        label='Assunto',
        max_length=180,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    message = forms.CharField(
        label='Mensagem',
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
                'rows': 9,
                'placeholder': 'Escreva o comunicado coletivo.',
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get('recipient_group')
        turma = cleaned_data.get('turma')
        if group in {
            EmailCommunication.RecipientGroup.ALUNOS_TURMA,
            EmailCommunication.RecipientGroup.PROFESSORES_TURMA,
        } and not turma:
            raise forms.ValidationError('Selecione a turma para este envio em massa.')
        return cleaned_data


class EmailBulkForm(EmailScheduleMixin, EmailBulkBaseForm):
    pass


class EmailTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailTemplate
        fields = ['name', 'category', 'default_subject', 'default_body', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'default_subject': forms.TextInput(attrs={'class': 'form-control'}),
            'default_body': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class PanelNoticeForm(forms.ModelForm):
    send_email = forms.BooleanField(
        label='Também enviar por email',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    email_recipient_group = forms.ChoiceField(
        label='Destinatários do email',
        required=False,
        choices=[
            ('', 'Usar público-alvo do aviso'),
            (EmailCommunication.RecipientGroup.TODOS_ALUNOS, 'Todos os alunos'),
            (EmailCommunication.RecipientGroup.TODOS_PROFESSORES, 'Todos os professores'),
            (EmailCommunication.RecipientGroup.TODOS_RESPONSAVEIS, 'Todos os responsáveis'),
            (EmailCommunication.RecipientGroup.ALUNOS_TURMA, 'Alunos da turma selecionada'),
            (EmailCommunication.RecipientGroup.PROFESSORES_TURMA, 'Professores da turma selecionada'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = PanelNotice
        fields = [
            'title', 'summary', 'content', 'category', 'audience', 'turma',
            'is_featured', 'is_visible', 'published_at',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'audience': forms.Select(attrs={'class': 'form-control'}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'published_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('published_at') and not getattr(self.instance, 'pk', None):
            self.initial['published_at'] = timezone.now().strftime('%Y-%m-%dT%H:%M')


class CalendarEventForm(forms.ModelForm):
    create_notice = forms.BooleanField(
        label='Publicar aviso relacionado no blog/painel',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    send_email = forms.BooleanField(
        label='Também enviar por email',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    email_recipient_group = forms.ChoiceField(
        label='Destinatários do email',
        required=False,
        choices=[
            ('', 'Usar público-alvo do evento'),
            (EmailCommunication.RecipientGroup.TODOS_ALUNOS, 'Todos os alunos'),
            (EmailCommunication.RecipientGroup.TODOS_PROFESSORES, 'Todos os professores'),
            (EmailCommunication.RecipientGroup.TODOS_RESPONSAVEIS, 'Todos os responsáveis'),
            (EmailCommunication.RecipientGroup.ALUNOS_TURMA, 'Alunos da turma selecionada'),
            (EmailCommunication.RecipientGroup.PROFESSORES_TURMA, 'Professores da turma selecionada'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = CalendarEvent
        fields = [
            'title', 'description', 'event_type', 'starts_at', 'ends_at',
            'location', 'audience', 'turma', 'is_featured', 'is_visible',
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'starts_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'ends_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'audience': forms.Select(attrs={'class': 'form-control'}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        starts_at = cleaned_data.get('starts_at')
        ends_at = cleaned_data.get('ends_at')
        if starts_at and ends_at and ends_at < starts_at:
            self.add_error('ends_at', 'A data de fim não pode ser anterior ao início.')
        return cleaned_data


# StudentAdminForm: ModelForm if model exists, otherwise a fallback Form
try:
    StudentModel = apps.get_model('students', 'Student')
except LookupError:
    StudentModel = None

if StudentModel:
    # escolher campos comuns se existirem
    common_fields = [
        f
        for f in (
            'first_name',
            'last_name',
            'full_name',
            'name',
            'email',
            'enrollment_number',
            'matricula',
        )
        if hasattr(StudentModel, f)
    ]
    fields = common_fields or '__all__'

    class StudentAdminForm(forms.ModelForm):
        class Meta:
            model = StudentModel
            fields = fields
else:
    class StudentAdminForm(forms.Form):
        name = forms.CharField(max_length=150, label='Nome')
        email = forms.EmailField(required=False)
        enrollment_number = forms.CharField(
            max_length=50,
            required=False,
            label='Número de matrícula',
        )


# Tentar obter modelos dinamicamente para tolerância
Enrollment = None
Course = None
PreRegistration = None
Student = None
try:
    Course = apps.get_model('courses', 'Disciplina')
except LookupError:
    try:
        Course = apps.get_model('courses', 'Discipline')
    except LookupError:
        Course = None
try:
    Enrollment = apps.get_model('courses', 'Enrollment')
except LookupError:
    Enrollment = None
try:
    PreRegistration = apps.get_model('students', 'PreRegistration')
except LookupError:
    PreRegistration = None
try:
    Student = apps.get_model('students', 'Student')
except LookupError:
    Student = None

if Enrollment:
    class EnrollmentForm(forms.ModelForm):
        # Dados pessoais
        first_name = forms.CharField(
            label='Nome', required=False, max_length=150
        )
        last_name = forms.CharField(
            label='Sobrenome', required=False, max_length=150
        )
        birth_date = forms.DateField(
            label='Data de Nascimento',
            required=False,
            widget=forms.DateInput(attrs={'type': 'date'}),
        )
        gender = forms.ChoiceField(
            label='Gênero',
            required=False,
            choices=[
                ('', '--'),
                ('M', 'Masculino'),
                ('F', 'Feminino'),
                ('O', 'Outro'),
            ],
        )
        cpf = forms.CharField(label='CPF', required=False, max_length=20)
        rg = forms.CharField(label='RG', required=False, max_length=30)
        social_name = forms.CharField(
            label='Nome Social', required=False, max_length=150
        )
        pronouns = forms.CharField(
            label='Pronomes', required=False, max_length=50
        )

        # Contatos
        phone = forms.CharField(
            label='Telefone', required=False, max_length=30
        )
        email = forms.EmailField(label='E-mail', required=False)

        # Dados do responsável
        responsible_name = forms.CharField(
            label='Nome do Responsável', required=False, max_length=150
        )
        responsible_phone = forms.CharField(
            label='Telefone do Responsável', required=False, max_length=30
        )
        responsible_email = forms.EmailField(
            label='E-mail do responsável', required=False
        )

        # Perfil escolar
        previous_school = forms.CharField(
            label='Escola Anterior', required=False, max_length=255
        )
        previous_grade = forms.CharField(
            label='Série/Curso Anterior', required=False, max_length=80
        )
        graduation_year = forms.CharField(
            label='Ano de Conclusão', required=False, max_length=10
        )

        # Contatos de emergência
        emergency_contact_name = forms.CharField(
            label='Contato de Emergência', required=False, max_length=150
        )
        emergency_contact_phone = forms.CharField(
            label='Telefone Emergência', required=False, max_length=30
        )
        emergency_contact_relation = forms.CharField(
            label='Grau de Parentesco', required=False, max_length=80
        )

        # Endereço
        address = forms.CharField(
            label='Endereço', required=False, max_length=255
        )
        city = forms.CharField(label='Cidade', required=False, max_length=100)
        state = forms.CharField(label='Estado', required=False, max_length=50)
        zip_code = forms.CharField(label='CEP', required=False, max_length=20)

        # Pré-matrícula opcional
        pre_registration = forms.ModelChoiceField(
            queryset=(
                PreRegistration.objects.all()
                if PreRegistration is not None
                else ()
            ),
            required=False,
            label='Pré-matrícula (opcional)',
        )

        field_order = [
            'first_name',
            'last_name',
            'birth_date',
            'gender',
            'cpf',
            'rg',
            'social_name',
            'pronouns',
            'phone',
            'email',
            'responsible_name',
            'responsible_phone',
            'responsible_email',
            'previous_school',
            'previous_grade',
            'graduation_year',
            'emergency_contact_name',
            'emergency_contact_phone',
            'emergency_contact_relation',
            'address',
            'city',
            'state',
            'zip_code',
            'pre_registration',
        ]

        field_groups = [
            ('Dados Pessoais', [
                'first_name', 'last_name', 'birth_date', 'gender', 'cpf', 'rg',
                'social_name', 'pronouns',
            ]),
            ('Contatos', ['phone', 'email']),
            ('Dados do Responsável', [
                'responsible_name', 'responsible_phone', 'responsible_email',
            ]),
            ('Perfil Escolar', [
                'previous_school', 'previous_grade', 'graduation_year',
            ]),
            ('Contato de Emergência', [
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relation',
            ]),
            ('Endereço', ['address', 'city', 'state', 'zip_code']),
            ('Pré-matrícula', ['pre_registration']),
        ]

        class Meta:
            model = Enrollment
            exclude = ('student',)

        @staticmethod
        def _split_name(full_name):
            name_parts = (full_name or '').strip().split()
            if not name_parts:
                return '', ''
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
            return first_name, last_name

        @staticmethod
        def _normalize_state(value):
            raw = (value or '').strip().upper()
            if not raw:
                return ''
            if len(raw) == 2:
                return raw
            if '-' in raw:
                maybe_state = raw.split('-')[-1].strip()
                if len(maybe_state) == 2:
                    return maybe_state
            return raw[:2]

        def _apply_pre_registration_initial(self, pre_registration):
            if not pre_registration:
                return

            first_name, last_name = self._split_name(getattr(pre_registration, 'name', ''))
            initial_map = {
                'first_name': first_name,
                'last_name': last_name,
                'birth_date': getattr(pre_registration, 'birth_date', None),
                'gender': getattr(pre_registration, 'gender', ''),
                'cpf': getattr(pre_registration, 'cpf', ''),
                'rg': getattr(pre_registration, 'rg', ''),
                'social_name': getattr(pre_registration, 'social_name', ''),
                'pronouns': getattr(pre_registration, 'pronouns', ''),
                'phone': getattr(pre_registration, 'phone', ''),
                'email': getattr(pre_registration, 'email', ''),
                'responsible_name': getattr(pre_registration, 'responsible_name', ''),
                'responsible_phone': getattr(pre_registration, 'responsible_phone', ''),
                'responsible_email': getattr(pre_registration, 'responsible_email', ''),
                'emergency_contact_name': getattr(pre_registration, 'responsible_name', ''),
                'emergency_contact_phone': getattr(pre_registration, 'responsible_phone', ''),
                'address': getattr(pre_registration, 'address', ''),
                'city': getattr(pre_registration, 'city', ''),
                'state': self._normalize_state(getattr(pre_registration, 'state', '')),
                'zip_code': getattr(pre_registration, 'zip_code', ''),
                'graduation_year': getattr(pre_registration, 'graduation_year', ''),
            }

            for field_name, field_value in initial_map.items():
                if field_name in self.fields and field_value not in (None, ''):
                    self.initial.setdefault(field_name, field_value)
                    self.fields[field_name].initial = field_value

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for name, field in self.fields.items():
                widget = field.widget
                css = 'form-control'
                if (
                    isinstance(widget, (forms.Select, forms.NullBooleanSelect))
                    or name == 'pre_registration'
                ):
                    css = 'form-select'
                if widget.attrs.get('class'):
                    widget.attrs['class'] = f"{widget.attrs['class']} {css}"
                else:
                    widget.attrs['class'] = css
                if name == 'birth_date':
                    widget.attrs['type'] = 'date'
                if not widget.attrs.get('placeholder'):
                    widget.attrs['placeholder'] = field.label

            pre_registration = None
            pre_registration_id = self.initial.get('pre_registration')
            if not pre_registration_id and self.is_bound:
                pre_registration_id = self.data.get('pre_registration')
            if pre_registration_id and PreRegistration is not None:
                with suppress(Exception):
                    pre_registration = PreRegistration.objects.filter(
                        id=pre_registration_id
                    ).first()
            self._apply_pre_registration_initial(pre_registration)

            # computar campos não agrupados
            all_field_names = list(self.fields.keys())
            grouped = []
            for grp in getattr(self, 'field_groups', []):
                if isinstance(grp, (list, tuple)) and len(grp) > 1:
                    with suppress(Exception):
                        grouped.extend(grp[1])
            self.other_fields = [
                f
                for f in all_field_names
                if f not in grouped
            ]

        def clean(self):
            cleaned_data = super().clean()
            pr = cleaned_data.get('pre_registration')

            if pr:
                first_name = (cleaned_data.get('first_name') or '').strip()
                last_name = (cleaned_data.get('last_name') or '').strip()
                email = (cleaned_data.get('email') or '').strip()
                phone = (cleaned_data.get('phone') or '').strip()

                if not first_name:
                    fallback_first_name, fallback_last_name = self._split_name(pr.name)
                    cleaned_data['first_name'] = fallback_first_name
                    if not last_name:
                        cleaned_data['last_name'] = fallback_last_name

                if not email:
                    cleaned_data['email'] = pr.email

                if not phone:
                    cleaned_data['phone'] = pr.phone

                fallback_map = {
                    'birth_date': getattr(pr, 'birth_date', None),
                    'cpf': getattr(pr, 'cpf', ''),
                    'rg': getattr(pr, 'rg', ''),
                    'social_name': getattr(pr, 'social_name', ''),
                    'pronouns': getattr(pr, 'pronouns', ''),
                    'responsible_name': getattr(pr, 'responsible_name', ''),
                    'responsible_phone': getattr(pr, 'responsible_phone', ''),
                    'responsible_email': getattr(pr, 'responsible_email', ''),
                    'emergency_contact_name': getattr(pr, 'responsible_name', ''),
                    'emergency_contact_phone': getattr(pr, 'responsible_phone', ''),
                    'address': getattr(pr, 'address', ''),
                    'city': getattr(pr, 'city', ''),
                    'state': self._normalize_state(getattr(pr, 'state', '')),
                    'zip_code': getattr(pr, 'zip_code', ''),
                    'graduation_year': getattr(pr, 'graduation_year', ''),
                }
                for field_name, fallback_value in fallback_map.items():
                    if not cleaned_data.get(field_name) and fallback_value not in (None, ''):
                        cleaned_data[field_name] = fallback_value

            if not cleaned_data.get('first_name'):
                raise forms.ValidationError('Informe o nome do aluno ou selecione um pré-cadastro válido.')

            if not cleaned_data.get('email'):
                raise forms.ValidationError('Informe o email do aluno ou selecione um pré-cadastro válido.')

            return cleaned_data

        def save(self, commit=True):
            with transaction.atomic():
                enrollment = super().save(commit=False)
                pr = None
                if hasattr(self, 'cleaned_data'):
                    pr = self.cleaned_data.get('pre_registration')

                first_name = (self.cleaned_data.get('first_name') or '').strip()
                last_name = (self.cleaned_data.get('last_name') or '').strip()
                email = (self.cleaned_data.get('email') or '').strip().lower()
                phone = (self.cleaned_data.get('phone') or '').strip()

                if pr:
                    if not first_name:
                        first_name, fallback_last_name = self._split_name(pr.name)
                        if not last_name:
                            last_name = fallback_last_name
                    if not email:
                        email = (pr.email or '').strip().lower()
                    if not phone:
                        phone = (pr.phone or '').strip()

                if not email:
                    raise ValidationError('Informe um email válido para criar a matrícula do aluno.')
                if not first_name:
                    raise ValidationError('Informe ao menos o nome do aluno para concluir a matrícula.')

                username_base = email.split('@')[0].replace(' ', '').lower() or 'aluno'
                username = username_base
                suffix = 1
                while User.objects.exclude(email=email).filter(username=username).exists():
                    suffix += 1
                    username = f'{username_base}{suffix}'

                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        'username': username,
                        'first_name': first_name,
                        'last_name': last_name,
                        'phone': phone,
                        'user_type': User.UserType.ALUNO,
                        'is_active': True,
                    },
                )

                if not created:
                    user_changed = False
                    if user.user_type != User.UserType.ALUNO and not hasattr(user, 'student_profile'):
                        raise ValidationError(
                            'Já existe um usuário com este email vinculado a outro perfil do sistema.'
                        )
                    if first_name and user.first_name != first_name:
                        user.first_name = first_name
                        user_changed = True
                    if last_name and user.last_name != last_name:
                        user.last_name = last_name
                        user_changed = True
                    if phone and user.phone != phone:
                        user.phone = phone
                        user_changed = True
                    if user.user_type != User.UserType.ALUNO and hasattr(user, 'student_profile'):
                        user.user_type = User.UserType.ALUNO
                        user_changed = True
                    if user_changed:
                        user.save()

                student_obj = None
                if Student:
                    student_defaults = {
                        'birth_date': self.cleaned_data.get('birth_date') or getattr(pr, 'birth_date', None),
                        'cpf': self.cleaned_data.get('cpf') or getattr(pr, 'cpf', ''),
                        'rg': self.cleaned_data.get('rg') or getattr(pr, 'rg', ''),
                        'address': self.cleaned_data.get('address') or getattr(pr, 'address', ''),
                        'city': self.cleaned_data.get('city') or getattr(pr, 'city', ''),
                        'state': self._normalize_state(
                            self.cleaned_data.get('state') or getattr(pr, 'state', '')
                        ),
                        'zip_code': self.cleaned_data.get('zip_code') or getattr(pr, 'zip_code', ''),
                        'emergency_contact_name': self.cleaned_data.get('emergency_contact_name') or getattr(pr, 'responsible_name', ''),
                        'emergency_contact_phone': self.cleaned_data.get('emergency_contact_phone') or getattr(pr, 'responsible_phone', ''),
                        'responsible_name': self.cleaned_data.get('responsible_name') or getattr(pr, 'responsible_name', ''),
                        'responsible_phone': self.cleaned_data.get('responsible_phone') or getattr(pr, 'responsible_phone', ''),
                        'responsible_email': self.cleaned_data.get('responsible_email') or getattr(pr, 'responsible_email', ''),
                        'is_active': bool(self.cleaned_data.get('is_active', True)),
                        'status': getattr(Student.Status, 'CURSANDO', 'CURSANDO'),
                    }

                    student_obj, _ = Student.objects.get_or_create(
                        user=user,
                        defaults=student_defaults,
                    )

                    student_changed = False
                    for field_name, field_value in student_defaults.items():
                        if field_value not in (None, '') and getattr(student_obj, field_name, None) != field_value:
                            setattr(student_obj, field_name, field_value)
                            student_changed = True

                    notes_parts = []
                    if pr:
                        notes_parts.append(f'Pré-cadastro #{pr.id}: {pr.name}')
                    if self.cleaned_data.get('notes'):
                        notes_parts.append(self.cleaned_data['notes'])
                    if hasattr(student_obj, 'notes') and notes_parts:
                        merged_notes = '\n'.join(part for part in notes_parts if part).strip()
                        if merged_notes and merged_notes not in (student_obj.notes or ''):
                            student_obj.notes = '\n'.join(
                                part for part in [student_obj.notes, merged_notes] if part
                            ).strip()
                            student_changed = True

                    if student_changed:
                        student_obj.save()

                if student_obj:
                    existing_enrollment = Enrollment.objects.filter(
                        student=student_obj,
                        course=enrollment.course,
                    ).exclude(pk=enrollment.pk).first()
                    if existing_enrollment:
                        existing_enrollment.turma = enrollment.turma
                        existing_enrollment.is_active = enrollment.is_active
                        existing_enrollment.notes = enrollment.notes
                        existing_enrollment.save()
                        enrollment = existing_enrollment
                    else:
                        enrollment.student = student_obj

                if commit and student_obj:
                    if enrollment.pk is None:
                        enrollment.save()
                    try:
                        extras_keys = [
                            'responsible_name',
                            'responsible_phone',
                            'responsible_email',
                            'previous_school',
                            'previous_grade',
                            'emergency_contact_name',
                            'emergency_contact_phone',
                            'emergency_contact_relation',
                            'address',
                            'city',
                            'state',
                            'zip_code',
                        ]

                        extras = {
                            k: v
                            for k in extras_keys
                            if (v := self.cleaned_data.get(k))
                        }

                        if getattr(student_obj, '_meta', None):
                            valid_obj_field_names = [
                                f.name for f in student_obj._meta.get_fields()
                            ]
                        else:
                            valid_obj_field_names = []

                        for k, v in extras.items():
                            cond = (
                                hasattr(student_obj, k)
                                or (
                                    valid_obj_field_names
                                    and k in valid_obj_field_names
                                )
                            )
                            if cond:
                                setattr(student_obj, k, v)
                        student_obj.save()
                    except Exception:
                        pass

                    if pr:
                        pr.is_reviewed = True
                        with suppress(Exception):
                            from django.utils import timezone
                            pr.reviewed_at = timezone.now()
                        pr.save(update_fields=['is_reviewed', 'reviewed_at'])

                return enrollment
else:
    # Fallback: formulário simples que avisa que Enrollment não foi encontrado
    class EnrollmentForm(forms.Form):
        error = forms.CharField(
            required=False,
            widget=forms.HiddenInput(),
            initial='Enrollment model not available',
        )


# Adicionar formulário de cadastro de professores estruturado
try:
    TeacherModel = apps.get_model('teachers', 'Teacher')
except LookupError:
    TeacherModel = None

if TeacherModel:
    class TeacherRegistrationForm(forms.ModelForm):
        # Dados pessoais
        first_name = forms.CharField(
            label='Nome',
            required=True,
            max_length=150,
        )
        last_name = forms.CharField(
            label='Sobrenome',
            required=False,
            max_length=150,
        )
        birth_date = forms.DateField(
            label='Data de Nascimento',
            required=False,
            widget=forms.DateInput(attrs={'type': 'date'}),
        )
        cpf = forms.CharField(label='CPF', required=False, max_length=20)

        # Contato
        phone = forms.CharField(
            label='Telefone',
            required=False,
            max_length=30,
        )
        email = forms.EmailField(label='E-mail', required=False)

        # Formação acadêmica
        highest_degree = forms.CharField(
            label='Formação (Grau Máximo)', required=False, max_length=255
        )
        institution = forms.CharField(
            label='Instituição', required=False, max_length=255
        )
        graduation_year = forms.CharField(
            label='Ano de Conclusão', required=False, max_length=10
        )

        # Experiência profissional
        experience_summary = forms.CharField(
            label='Resumo da Experiência',
            required=False,
            widget=forms.Textarea(attrs={'rows': 4}),
        )
        years_experience = forms.IntegerField(
            label='Anos de experiência',
            required=False,
        )

        # Endereço
        address = forms.CharField(
            label='Endereço', required=False, max_length=255
        )
        city = forms.CharField(label='Cidade', required=False, max_length=100)
        state = forms.CharField(label='Estado', required=False, max_length=50)
        zip_code = forms.CharField(label='CEP', required=False, max_length=20)

        # Contato de emergência
        emergency_contact_name = forms.CharField(
            label='Contato de Emergência',
            required=False,
            max_length=150,
        )
        emergency_contact_phone = forms.CharField(
            label='Telefone de Emergência',
            required=False,
            max_length=30,
        )
        emergency_contact_relation = forms.CharField(
            label='Grau de Parentesco',
            required=False,
            max_length=80,
        )

        # Ordem e agrupamentos
        field_order = [
            'first_name', 'last_name', 'birth_date', 'cpf',
            'phone', 'email',
            'responsible_name', 'responsible_phone', 'responsible_email',
            'highest_degree', 'institution', 'graduation_year',
            'experience_summary', 'years_experience',
            'address', 'city', 'state', 'zip_code',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation',
        ]

        field_groups = [
            ('Dados Pessoais', [
                'first_name', 'last_name', 'birth_date', 'cpf',
            ]),
            ('Contatos', ['phone', 'email']),
            ('Formação Acadêmica', [
                'highest_degree', 'institution', 'graduation_year',
            ]),
            ('Experiência Profissional', [
                'experience_summary', 'years_experience',
            ]),
            ('Endereço', [
                'address', 'city', 'state', 'zip_code',
            ]),
            ('Contato de Emergência', [
                'emergency_contact_name', 'emergency_contact_phone',
                'emergency_contact_relation',
            ]),
        ]

        class Meta:
            model = TeacherModel
            fields = '__all__'

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for name, field in self.fields.items():
                widget = field.widget
                css = 'form-control'
                if isinstance(widget, (forms.Select, forms.NullBooleanSelect)):
                    css = 'form-select'
                if widget.attrs.get('class'):
                    widget.attrs['class'] = f"{widget.attrs['class']} {css}"
                else:
                    widget.attrs['class'] = css
                if name == 'birth_date':
                    widget.attrs['type'] = 'date'
                if not widget.attrs.get('placeholder'):
                    widget.attrs['placeholder'] = field.label

            # calcular outros campos não agrupados
            all_field_names = list(self.fields.keys())
            grouped = []
            for grp in getattr(self, 'field_groups', []):
                with suppress(Exception):
                    grouped.extend(grp[1])
            # manter a ordem original dos campos não agrupados
            self.other_fields = [
                f for f in all_field_names if f not in grouped
            ]

        def save(self, commit=True):
            inst = super().save(commit=False)
            if commit:
                inst.save()
            return inst

    # Substituir/exportar TeacherForm pelo novo formulário
    TeacherForm = TeacherRegistrationForm
else:
    # manter fallback
    TeacherForm = get_model_form('teachers', 'Teacher') or forms.Form


__all__ = [
    'get_model_form',
    'StudentForm',
    'TeacherForm',
    'DisciplineForm',
    'EnrollmentForm',
    'StudentAdminForm',
]
