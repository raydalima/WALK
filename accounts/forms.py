from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User
from students.models import Student
from teachers.models import Teacher

class CustomLoginForm(AuthenticationForm):
    """Formulário de login customizado"""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite seu e-mail',
            'autofocus': True
        }),
        label='E-mail'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        }),
        label='Senha'
    )

class UserRegistrationForm(UserCreationForm):
    """Formulário para registro de novos usuários"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-mail'})
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sobrenome'})
    )
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone'})
    )
    user_type = forms.ChoiceField(
        choices=User.UserType.choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Usuário'
    )
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'phone', 'user_type', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome de usuário'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Senha'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirme a senha'})

class StudentProfileForm(forms.ModelForm):
    """Formulário para perfil de aluno"""
    class Meta:
        model = Student
        fields = [
            'birth_date', 'cpf', 'rg', 'address', 'city', 'state', 'zip_code',
            'enrollment_number', 'status', 'approved_course', 'exit_reason',
            'emergency_contact_name', 'emergency_contact_phone', 'notes'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '2'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '00000-000'}),
            'enrollment_number': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'approved_course': forms.TextInput(attrs={'class': 'form-control'}),
            'exit_reason': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TeacherProfileForm(forms.ModelForm):
    """Formulário para perfil de professor"""
    class Meta:
        model = Teacher
        fields = [
            'specialization', 'bio', 'education', 'experience_years',
            'professional_email', 'lattes_url', 'knowledge_areas',
            'availability', 'contact_notes'
        ]
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'education': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'professional_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'lattes_url': forms.URLInput(attrs={'class': 'form-control'}),
            'knowledge_areas': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'availability': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
