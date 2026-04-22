from django.contrib import admin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'author', 'publish_date', 'is_published', 'views_count']
    list_filter = ['category', 'is_published', 'publish_date']
    search_fields = ['title', 'content', 'author__first_name', 'author__last_name']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    
    fieldsets = (
        ('Conteúdo', {
            'fields': ('title', 'slug', 'category', 'content', 'excerpt')
        }),
        ('Imagem', {
            'fields': ('featured_image',)
        }),
        ('Publicação', {
            'fields': ('author', 'is_published')
        }),
        ('Estatísticas', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['views_count']
