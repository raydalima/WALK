from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class Teacher(models.Model):
    """Modelo para perfil de professor"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name='Usuário'
    )
    
    # Informações profissionais
    specialization = models.CharField(
        max_length=200,
        verbose_name='Especialização',
        blank=True
    )
    bio = models.TextField(verbose_name='Biografia', blank=True)
    
    # Formação acadêmica
    education = models.TextField(verbose_name='Formação Acadêmica', blank=True)
    experience_years = models.IntegerField(
        verbose_name='Anos de Experiência',
        default=0
    )
    
    # Contato profissional
    professional_email = models.EmailField(
        verbose_name='E-mail profissional',
        blank=True
    )
    lattes_url = models.URLField(
        verbose_name='Link do Currículo Lattes',
        blank=True
    )
    knowledge_areas = models.ManyToManyField(
        'courses.AreaConhecimento',
        blank=True,
        related_name='teachers',
        verbose_name='Áreas do Conhecimento',
    )
    availability = models.TextField(
        verbose_name='Disponibilidade',
        blank=True,
    )
    contact_notes = models.TextField(
        verbose_name='Observações de Contato',
        blank=True,
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    hire_date = models.DateField(
        auto_now_add=True,
        verbose_name='Data de Contratação'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Professor'
        verbose_name_plural = 'Professores'
        ordering = ['-hire_date']
    
    def __str__(self):
        return f"Prof. {self.user.get_full_name()}"
    
    def get_courses(self):
        """Retorna todas as disciplinas do professor"""
        return self.courses.filter(is_active=True)
