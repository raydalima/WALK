from django import forms

from utils.external_links import EXTERNAL_LINK_HELP_TEXT, validate_external_resource_url

from .models import ActivityResult, EssaySubmission


class StudentEssaySubmissionForm(forms.ModelForm):
    class Meta:
        model = EssaySubmission
        fields = ['course', 'title', 'prompt', 'submission_url']
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Ex.: Redação sobre cidadania digital',
                }
            ),
            'prompt': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Tema ou proposta de redação.',
                }
            ),
            'submission_url': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://docs.google.com/...',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        course_queryset = kwargs.pop('course_queryset', None)
        super().__init__(*args, **kwargs)
        if course_queryset is not None:
            self.fields['course'].queryset = course_queryset
        self.fields['course'].label = 'Disciplina'
        self.fields['title'].label = 'Título'
        self.fields['prompt'].label = 'Tema / proposta'
        self.fields['submission_url'].label = 'Link da redação'
        self.fields['submission_url'].help_text = EXTERNAL_LINK_HELP_TEXT

    def clean(self):
        cleaned_data = super().clean()
        submission_url = cleaned_data.get('submission_url')
        if not submission_url:
            raise forms.ValidationError(
                'Cole o link da sua redação no Google Docs, Drive ou outra nuvem.'
            )
        validate_external_resource_url(submission_url)
        return cleaned_data


class EssayCorrectionForm(forms.ModelForm):
    class Meta:
        model = EssaySubmission
        fields = ['score', 'teacher_feedback', 'status']
        widgets = {
            'score': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.5'}
            ),
            'teacher_feedback': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 10,
                    'placeholder': 'Escreva o feedback da correção para o aluno.',
                }
            ),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['score'].label = 'Nota'
        self.fields['teacher_feedback'].label = 'Feedback da correção'
        self.fields['status'].label = 'Situação'


class StudentActivitySubmissionForm(forms.ModelForm):
    class Meta:
        model = ActivityResult
        fields = ['submission_url', 'notes']
        widgets = {
            'submission_url': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://docs.google.com/...',
                }
            ),
            'notes': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Observações para o professor, se necessário.',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['submission_url'].label = 'Link da atividade'
        self.fields['submission_url'].help_text = EXTERNAL_LINK_HELP_TEXT
        self.fields['notes'].label = 'Observação do aluno'
        self.fields['notes'].required = False

    def clean_submission_url(self):
        value = self.cleaned_data.get('submission_url')
        if not value:
            raise forms.ValidationError('Cole o link da atividade antes de enviar.')
        validate_external_resource_url(value)
        return value


class TeacherActivityCorrectionForm(forms.ModelForm):
    class Meta:
        model = ActivityResult
        fields = ['status', 'teacher_feedback', 'score']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'teacher_feedback': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 7,
                    'placeholder': 'Feedback para o aluno.',
                }
            ),
            'score': forms.NumberInput(
                attrs={'class': 'form-control', 'min': 0, 'max': 100, 'step': '0.5'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].label = 'Situação da correção'
        self.fields['teacher_feedback'].label = 'Feedback do professor'
        self.fields['score'].label = 'Nota'
        self.fields['score'].required = False
