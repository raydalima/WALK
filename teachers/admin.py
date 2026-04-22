from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'specialization', 'experience_years', 'is_active', 'hire_date']
    list_filter = ['is_active', 'hire_date']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'specialization']
    date_hierarchy = 'hire_date'
    
    fieldsets = (
        ('Usuário', {
            'fields': ('user',)
        }),
        ('Informações Profissionais', {
            'fields': ('specialization', 'bio', 'education', 'experience_years')
        }),
        ('Contato Profissional', {
            'fields': ('professional_email', 'lattes_url')
        }),
        ('Situação', {
            'fields': ('is_active',)
        }),
    )
    
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Nome Completo'
