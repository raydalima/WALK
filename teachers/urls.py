from django.urls import include, path

from . import views

app_name = 'teachers'

urlpatterns = [
    path('', views.dashboard, name='root'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('minhas-disciplinas/', views.my_courses, name='my_courses'),

    path(
        'disciplina/<int:course_id>/alunos/',
        views.course_students,
        name='course_students',
    ),
    path(
        'disciplina/<int:course_id>/frequencia/',
        views.course_attendance,
        name='course_attendance',
    ),
    path(
        'disciplina/<int:course_id>/frequencia/csv/',
        views.course_attendance_csv,
        name='course_attendance_csv',
    ),

    path(
        'aluno/<int:student_id>/diagnostico/',
        views.student_diagnostic,
        name='student_diagnostic',
    ),
    path(
        'aluno/<int:student_id>/feedback/',
        views.student_feedback,
        name='student_feedback',
    ),

    path('correcoes/', views.corrections_home, name='corrections_home'),
    path('atividades/', views.activity_submissions_list, name='activity_submissions_list'),
    path(
        'atividades/<int:activity_id>/',
        views.activity_submissions_detail,
        name='activity_submissions_detail',
    ),
    path(
        'atividades/<int:activity_id>/aluno/<int:student_id>/corrigir/',
        views.activity_result_update,
        name='activity_result_update',
    ),
    path(
        'correcoes/redacao/<int:essay_id>/',
        views.essay_correction_detail,
        name='essay_correction_detail',
    ),

    path(
        'disciplina/<int:course_id>/materiais/',
        views.course_materials,
        name='course_materials',
    ),
    path(
        'disciplina/<int:course_id>/upload-material/',
        views.upload_material,
        name='upload_material',
    ),
    path(
        'material/<int:material_id>/deletar/',
        views.delete_material,
        name='delete_material',
    ),
    path(
        'disciplina/<int:course_id>/videos/',
        views.course_videos,
        name='course_videos',
    ),
    path(
        'disciplina/<int:course_id>/adicionar-video/',
        views.add_video,
        name='add_video',
    ),
    path(
        'video/<int:video_id>/deletar/',
        views.delete_video,
        name='delete_video',
    ),

    path('questionarios/', include('assessments.teacher_urls')),

    # Conteúdos
    path('conteudos/', views.materials_list, name='materials_list'),

    # Frequência
    path('frequencia/', views.attendance_home, name='attendance_home'),
]

urlpatterns += [
    path(
        'frequencia/<int:course_id>/',
        views.attendance_course,
        name='attendance_course',
    ),
    path(
        'frequencia/<int:course_id>/nova/',
        views.attendance_session_create,
        name='attendance_session_create',
    ),
    path(
        'frequencia/sessao/<int:session_id>/',
        views.attendance_session_detail,
        name='attendance_session_detail',
    ),
    path(
        'frequencia/sessao/<int:session_id>/csv/',
        views.attendance_session_csv,
        name='attendance_session_csv',
    ),
    path(
        'frequencia/sessao/<int:session_id>/pdf/',
        views.attendance_session_pdf,
        name='attendance_session_pdf',
    ),
]
