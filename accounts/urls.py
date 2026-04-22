from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path(
        'login/',
        views.login_view,
        name='login',
    ),
    path(
        'logout/',
        views.logout_view,
        name='logout',
    ),
    path(
        'dashboard-redirect/',
        views.dashboard_redirect,
        name='dashboard_redirect',
    ),
    path(
        'login/aluno/',
        views.login_student_page,
        name='login_student',
    ),
    path(
        'login/professor/',
        views.login_teacher_page,
        name='login_teacher',
    ),
    path(
        'login/gestao/',
        views.login_gestao_page,
        name='login_gestao',
    ),
]
