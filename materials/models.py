from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from courses.models import Course
from utils.external_links import validate_external_resource_url

class Material(models.Model):
    """Materiais de estudo armazenam apenas links externos."""
    
    class MaterialType(models.TextChoices):
        PDF = 'PDF', _('PDF')
        DOC = 'DOC', _('Documento Word')
        SLIDE = 'SLIDE', _('Apresentação')
        EXERCISE = 'EXERCISE', _('Lista de Exercícios')
        OTHER = 'OTHER', _('Outro')
    
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descrição', blank=True)
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='materials',
        verbose_name='Disciplina'
    )
    area = models.ForeignKey(
        'courses.AreaConhecimento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materials',
        verbose_name='Área de Conhecimento',
    )
    turma = models.ForeignKey(
        'courses.Turma',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='materials',
        verbose_name='Turma',
    )
    
    material_type = models.CharField(
        max_length=10,
        choices=MaterialType.choices,
        default=MaterialType.PDF,
        verbose_name='Tipo de Material'
    )
    
    external_url = models.URLField(
        verbose_name='Link externo',
        help_text='Link compartilhável do material hospedado em nuvem externa.',
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_materials',
        verbose_name='Enviado por'
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name='Data de cadastro')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Material'
        verbose_name_plural = 'Materiais'
        ordering = ['-upload_date']

    def __str__(self):
        course_name = getattr(self.course, 'nome', None) or str(self.course)
        return f"{self.title} - {course_name}"

    def clean(self):
        if not self.area_id and self.course_id:
            self.area = getattr(self.course, 'area', None)
        validate_external_resource_url(self.external_url)

    def save(self, *args, **kwargs):
        if not self.area_id and self.course_id:
            self.area = getattr(self.course, 'area', None)
        super().save(*args, **kwargs)
    
    def get_file_name(self):
        """Mantido por compatibilidade; agora retorna o link externo."""
        return self.external_url or ''

    @property
    def access_url(self):
        """Retorna a URL principal de acesso ao material."""
        return self.external_url

    @property
    def has_resource(self):
        """Indica se o material possui link externo disponível."""
        return bool(self.external_url)
    
    def get_file_size(self):
        """Compatibilidade visual para telas antigas."""
        return "Link externo"

class VideoLesson(models.Model):
    """Modelo para aulas em vídeo (links externos)"""
    
    class Platform(models.TextChoices):
        YOUTUBE = 'YOUTUBE', _('YouTube')
        VIMEO = 'VIMEO', _('Vimeo')
        OTHER = 'OTHER', _('Outro')
    
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(verbose_name='Descrição', blank=True)
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='video_lessons',
        verbose_name='Disciplina'
    )
    
    platform = models.CharField(
        max_length=10,
        choices=Platform.choices,
        default=Platform.YOUTUBE,
        verbose_name='Plataforma'
    )
    
    video_url = models.URLField(verbose_name='Link do Vídeo')
    
    duration = models.CharField(
        max_length=20,
        verbose_name='Duração',
        blank=True,
        help_text='Exemplo: 45 minutos'
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_videos',
        verbose_name='Cadastrado por'
    )
    
    # Ordem e organização
    lesson_number = models.IntegerField(
        verbose_name='Número da Aula',
        default=0,
        help_text='Para ordenação'
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Ativa')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Aula em Vídeo'
        verbose_name_plural = 'Aulas em Vídeo'
        ordering = ['course', 'lesson_number']

    def __str__(self):
        course_name = getattr(self.course, 'nome', None) or str(self.course)
        return f"Aula {self.lesson_number}: {self.title} - {course_name}"
    
    def get_embed_url(self):
        """Converte URL do vídeo para formato embed"""
        if self.platform == self.Platform.YOUTUBE:
            if 'watch?v=' in self.video_url:
                video_id = self.video_url.split('watch?v=')[1].split('&')[0]
                return f"https://www.youtube.com/embed/{video_id}"
            elif 'youtu.be/' in self.video_url:
                video_id = self.video_url.split('youtu.be/')[1].split('?')[0]
                return f"https://www.youtube.com/embed/{video_id}"
        elif self.platform == self.Platform.VIMEO:
            if 'vimeo.com/' in self.video_url:
                video_id = self.video_url.split('vimeo.com/')[1].split('/')[0]
                return f"https://player.vimeo.com/video/{video_id}"
        return self.video_url
