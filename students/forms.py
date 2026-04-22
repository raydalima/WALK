import re

from django import forms
from django.core.exceptions import ValidationError

from .models import PreRegistration


class PreRegistrationForm(forms.ModelForm):
    class Meta:
        model = PreRegistration
        fields = [
            'name',
            'social_name',
            'gender',
            'race_self_declaration',
            'pronouns',
            'birth_date',
            'cpf',
            'rg',
            'phone',
            'email',
            'address',
            'city',
            'state',
            'zip_code',
            'responsible_name',
            'responsible_phone',
            'responsible_cpf',
            'responsible_rg',
            'responsible_address',
            'responsible_relationship',
            'responsible_relationship_other',
            'school_situation',
            'school_type',
            'graduation_year',
            'has_taken_enem',
            'intended_course',
            'family_income_range',
            'household_members',
            'has_internet_at_home',
            'has_device',
            'works_currently',
            'receives_social_benefit',
            'has_private_study_space',
            'transportation_type',
            'housing_status',
            'weekly_study_hours',
            'how_did_you_hear',
            'why_join',
            'message',
            'consent',
        ]
        labels = {
            'name': 'Nome completo',
            'social_name': 'Nome social',
            'gender': 'Gênero',
            'race_self_declaration': 'Autodeclaração racial',
            'pronouns': 'Pronomes',
            'birth_date': 'Data de nascimento',
            'cpf': 'CPF',
            'rg': 'RG',
            'phone': 'Telefone / WhatsApp',
            'email': 'E-mail',
            'address': 'Endereço completo',
            'city': 'Cidade',
            'state': 'UF',
            'zip_code': 'CEP',
            'responsible_name': 'Nome do responsável',
            'responsible_phone': 'Telefone do responsável',
            'responsible_cpf': 'CPF do responsável',
            'responsible_rg': 'RG do responsável',
            'responsible_address': 'Endereço do responsável',
            'responsible_relationship': 'Vínculo com o responsável',
            'responsible_relationship_other': 'Outro vínculo',
            'school_situation': 'Situação escolar',
            'school_type': 'Tipo de escola',
            'graduation_year': 'Ano de conclusão do ensino médio',
            'has_taken_enem': 'Já fez ENEM ou vestibular?',
            'intended_course': 'Curso pretendido',
            'family_income_range': 'Renda familiar mensal',
            'household_members': 'Quantidade de pessoas na residência',
            'has_internet_at_home': 'Tem internet em casa?',
            'has_device': 'Possui computador ou celular para estudar?',
            'works_currently': 'Trabalha atualmente?',
            'receives_social_benefit': 'Recebe benefício social?',
            'has_private_study_space': 'Possui espaço adequado para estudar?',
            'transportation_type': 'Como se desloca para estudar?',
            'housing_status': 'Situação de moradia',
            'weekly_study_hours': 'Quanto tempo consegue estudar por semana?',
            'how_did_you_hear': 'Como conheceu o cursinho?',
            'why_join': 'Por que deseja participar do cursinho?',
            'message': 'Observações adicionais',
            'consent': 'Autorizo o uso dos dados para contato administrativo e processo de matrícula',
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu nome completo'}),
            'social_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'race_self_declaration': forms.Select(attrs={'class': 'form-select'}),
            'pronouns': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Somente números'}),
            'rg': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(99) 99999-9999'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seuemail@exemplo.com'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '2'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control'}),
            'responsible_name': forms.TextInput(attrs={'class': 'form-control'}),
            'responsible_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'responsible_cpf': forms.TextInput(attrs={'class': 'form-control'}),
            'responsible_rg': forms.TextInput(attrs={'class': 'form-control'}),
            'responsible_address': forms.TextInput(attrs={'class': 'form-control'}),
            'responsible_relationship': forms.Select(attrs={'class': 'form-select'}),
            'responsible_relationship_other': forms.TextInput(attrs={'class': 'form-control'}),
            'school_situation': forms.Select(attrs={'class': 'form-select'}),
            'school_type': forms.Select(attrs={'class': 'form-select'}),
            'graduation_year': forms.TextInput(attrs={'class': 'form-control'}),
            'has_taken_enem': forms.Select(attrs={'class': 'form-select'}),
            'intended_course': forms.TextInput(attrs={'class': 'form-control'}),
            'family_income_range': forms.Select(attrs={'class': 'form-select'}),
            'household_members': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'has_internet_at_home': forms.Select(attrs={'class': 'form-select'}),
            'has_device': forms.Select(attrs={'class': 'form-select'}),
            'works_currently': forms.Select(attrs={'class': 'form-select'}),
            'receives_social_benefit': forms.Select(attrs={'class': 'form-select'}),
            'has_private_study_space': forms.Select(attrs={'class': 'form-select'}),
            'transportation_type': forms.Select(attrs={'class': 'form-select'}),
            'housing_status': forms.Select(attrs={'class': 'form-select'}),
            'weekly_study_hours': forms.Select(attrs={'class': 'form-select'}),
            'how_did_you_hear': forms.TextInput(attrs={'class': 'form-control'}),
            'why_join': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'consent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_cpf(self):
        cpf = self.cleaned_data.get('cpf')
        if not cpf:
            return ''
        digits = re.sub(r'\D', '', cpf)
        if len(digits) != 11:
            raise ValidationError('CPF inválido: informe 11 dígitos.')
        if digits == digits[0] * 11:
            raise ValidationError('CPF inválido.')
        return digits

    def clean_responsible_cpf(self):
        cpf = self.cleaned_data.get('responsible_cpf')
        if not cpf:
            return ''
        digits = re.sub(r'\D', '', cpf)
        if len(digits) != 11:
            raise ValidationError('CPF do responsável inválido: informe 11 dígitos.')
        return digits

    def clean_household_members(self):
        value = self.cleaned_data.get('household_members')
        if value in (None, ''):
            return None
        if int(value) < 1:
            raise ValidationError('Informe pelo menos 1 pessoa na residência.')
        return value
