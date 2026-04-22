from django.urls import path
from django.views.generic import RedirectView
from . import views
from . import views_reports as reports

app_name = 'students'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('minhas-disciplinas/', views.my_courses, name='my_courses'),
    path(
        'disciplina/<int:course_id>/',
        views.course_detail,
        name='course_detail'
    ),
    # rota para materiais de uma disciplina
    # (compatibilidade com templates)
    path(
        'materiais/<int:course_id>/',
        views.materials_list,
        name='view_materials'
    ),
    # rota geral para todos os materiais das disciplinas matriculadas
    path('materiais/', views.materials_list, name='materials_list'),
    path('perfil/', views.profile, name='profile'),
    # rota de pré-matrícula (formulário)
    path('pre-cadastro/', views.pre_cadastro, name='pre_cadastro'),
    path(
        'pre-matricula/',
        views.pre_registration_submit,
        name='pre_registration_submit',
    ),
    path('aulas/', views.video_lessons_list, name='video_lessons_list'),
    path('redacoes/', views.essay_list, name='essay_list'),
    path('redacoes/enviar/', views.essay_submit, name='essay_submit'),
    path('atividades/', views.activity_list, name='activity_list'),
    path('atividades/<int:activity_id>/enviar/', views.activity_submit, name='activity_submit'),
    path(
        'simulados/',
        RedirectView.as_view(
            pattern_name='assessments:student_quiz_list',
            permanent=False,
        ),
        name='quiz_list',
    ),
    path('course/', views.course_list, name='course_list'),
    path(
        'course/<int:course_id>/export/doc/',
        reports.export_enrollment_doc,
        name='export_enrollment_doc'
    ),
    path(
        'course/<int:course_id>/export/pdf/',
        reports.export_enrollment_pdf,
        name='export_enrollment_pdf'
    ),
    path('obrigado/', views.thanks, name='thanks'),
]
