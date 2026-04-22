from django.urls import path

from . import teacher_views

app_name = 'assessments_teacher'

urlpatterns = [
    path('', teacher_views.quiz_list, name='quiz_list'),
    path('novo/', teacher_views.quiz_create, name='quiz_create'),
    path('quiz/<int:quiz_id>/', teacher_views.quiz_detail, name='quiz_detail'),
    path(
        'quiz/<int:quiz_id>/publicar/',
        teacher_views.quiz_publish,
        name='quiz_publish',
    ),
    path(
        'quiz/<int:quiz_id>/pergunta/nova/',
        teacher_views.question_create,
        name='question_create',
    ),
    path(
        'quiz/<int:quiz_id>/envios/',
        teacher_views.submission_list,
        name='submission_list',
    ),
    path(
        'envio/<int:submission_id>/corrigir/',
        teacher_views.grade_submission,
        name='grade_submission',
    ),
]
