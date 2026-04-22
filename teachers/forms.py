from django import forms
from materials.models import Material, VideoLesson
from utils.external_links import EXTERNAL_LINK_HELP_TEXT, validate_external_resource_url

class MaterialForm(forms.ModelForm):
    """Cadastro de materiais por link externo, sem upload local."""
    class Meta:
        model = Material
        fields = ['title', 'description', 'material_type', 'turma', 'external_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título do material'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
            'material_type': forms.Select(attrs={'class': 'form-control'}),
            'turma': forms.Select(attrs={'class': 'form-control'}),
            'external_url': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'https://drive.google.com/...',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        course = kwargs.pop('course', None)
        super().__init__(*args, **kwargs)
        self.fields['external_url'].label = 'Link do material'
        self.fields['external_url'].help_text = EXTERNAL_LINK_HELP_TEXT
        self.fields['turma'].required = False
        self.fields['turma'].empty_label = 'Todas as turmas da disciplina'
        if course is not None:
            self.fields['turma'].queryset = course.turmas.filter(is_active=True).order_by('-ano', 'nome')

    def clean(self):
        cleaned_data = super().clean()
        external_url = cleaned_data.get('external_url')
        if not external_url:
            raise forms.ValidationError('Cole o link externo do material antes de salvar.')
        validate_external_resource_url(external_url)
        return cleaned_data

class VideoLessonForm(forms.ModelForm):
    """Formulário para cadastro de aulas em vídeo"""
    class Meta:
        model = VideoLesson
        fields = ['title', 'description', 'platform', 'video_url', 'duration', 'lesson_number']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título da aula'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
            'platform': forms.Select(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.youtube.com/watch?v=...'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 45 minutos'}),
            'lesson_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número da aula'}),
        }
