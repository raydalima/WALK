from django.urls import path

from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.student_quiz_list, name='student_quiz_list'),
    path(
        'quiz/<int:quiz_id>/responder/',
        views.student_take_quiz,
        name='student_take_quiz',
    ),
]
