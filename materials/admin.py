from django.contrib import admin
from .models import Material, VideoLesson

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'area', 'turma', 'material_type', 'uploaded_by', 'upload_date', 'is_active']
    list_filter = ['material_type', 'is_active', 'upload_date', 'area', 'course', 'turma']
    search_fields = ['title', 'description', 'course__nome']
    date_hierarchy = 'upload_date'
    
    fieldsets = (
        ('Informações do Material', {
            'fields': ('title', 'description', 'material_type')
        }),
        ('Organização Acadêmica', {
            'fields': ('area', 'course', 'turma')
        }),
        ('Link externo', {
            'fields': ('external_url',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'is_active')
        }),
    )

@admin.register(VideoLesson)
class VideoLessonAdmin(admin.ModelAdmin):
    list_display = ['lesson_number', 'title', 'course', 'platform', 'duration', 'is_active']
    list_filter = ['platform', 'is_active', 'course']
    search_fields = ['title', 'description', 'course__nome']
    ordering = ['course', 'lesson_number']
    
    fieldsets = (
        ('Informações da Aula', {
            'fields': ('title', 'description', 'lesson_number')
        }),
        ('Disciplina', {
            'fields': ('course',)
        }),
        ('Vídeo', {
            'fields': ('platform', 'video_url', 'duration')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'is_active')
        }),
    )
