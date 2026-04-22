from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.urls import reverse

class BlogPost(models.Model):
    """Modelo para posts do blog (notícias, avisos, conteúdos)"""
    
    class Category(models.TextChoices):
        NEWS = 'NEWS', _('Notícia')
        ANNOUNCEMENT = 'ANNOUNCEMENT', _('Aviso')
        CONTENT = 'CONTENT', _('Conteúdo Preparatório')
        EVENT = 'EVENT', _('Evento')
        TIP = 'TIP', _('Dica de Estudo')
    
    title = models.CharField(max_length=200, verbose_name='Título')
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    
    category = models.CharField(
        max_length=15,
        choices=Category.choices,
        default=Category.NEWS,
        verbose_name='Categoria'
    )
    
    content = models.TextField(verbose_name='Conteúdo')
    excerpt = models.TextField(
        max_length=300,
        verbose_name='Resumo',
        blank=True,
        help_text='Breve descrição do post (aparece na listagem)'
    )
    
    featured_image = models.ImageField(
        upload_to='blog/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Imagem Destaque'
    )
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='blog_posts',
        verbose_name='Autor'
    )
    
    # Status de publicação
    is_published = models.BooleanField(default=True, verbose_name='Publicado')
    publish_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Publicação'
    )
    
    # SEO e visualizações
    views_count = models.IntegerField(default=0, verbose_name='Visualizações')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Publicação do Blog'
        verbose_name_plural = 'Publicações do Blog'
        ordering = ['-publish_date']
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.excerpt and self.content:
            self.excerpt = self.content[:297] + '...'
        super().save(*args, **kwargs)
    
    def increment_views(self):
        """Incrementa o contador de visualizações"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    def get_absolute_url(self):
        return reverse('blog:blog_detail', kwargs={'slug': self.slug})


class ImportantLink(models.Model):
    class Category(models.TextChoices):
        MEC = 'MEC', _('MEC')
        BOOKS = 'BOOKS', _('Livros e Bibliotecas')
        EXAMS = 'EXAMS', _('Vestibulares e ENEM')
        STUDY = 'STUDY', _('Estudos e Plataformas')
        OTHER = 'OTHER', _('Outro')

    title = models.CharField(max_length=160, verbose_name='Título')
    url = models.URLField(verbose_name='Link')
    description = models.TextField(blank=True, verbose_name='Descrição')
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.MEC,
        verbose_name='Categoria',
    )
    icon = models.CharField(
        max_length=40,
        blank=True,
        verbose_name='Ícone Bootstrap',
        help_text='Exemplo: bi-book ou bi-globe',
    )
    is_featured = models.BooleanField(default=False, verbose_name='Destacar')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    display_order = models.PositiveIntegerField(default=0, verbose_name='Ordem')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='important_links_created',
        verbose_name='Criado por',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')

    class Meta:
        verbose_name = 'Link Importante'
        verbose_name_plural = 'Links Importantes'
        ordering = ['-is_featured', 'display_order', 'title']

    def __str__(self):
        return self.title
