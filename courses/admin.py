from django.contrib import admin
from django.contrib.admin.sites import AlreadyRegistered
import contextlib
from .models import AreaConhecimento, Disciplina, Course, Enrollment

# Ajuste do admin para compatibilidade
# com o novo modelo Disciplina (antigo Course)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['nome', 'area']
    list_filter = ['area']
    search_fields = ['nome']
    ordering = ['nome']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'student', 'course', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['student__user__username', 'student__user__email']


@admin.register(AreaConhecimento)
class AreaConhecimentoAdmin(admin.ModelAdmin):
    list_display = ('get_nome_display', 'cor_identificacao')
    search_fields = ('nome',)


class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'area')
    list_filter = ('area',)
    search_fields = ('nome',)
    raw_id_fields = ('area',)


# Registrar Disciplina de forma segura (ignora registro duplicado)
with contextlib.suppress(AlreadyRegistered):
    admin.site.register(Disciplina, DisciplinaAdmin)
