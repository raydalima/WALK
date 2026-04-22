from django.urls import path
from django.views.generic import TemplateView, RedirectView
from students import views as students_views

urlpatterns = [
    # ...existing url patterns...
    path(
        'students/dashboard/',
        TemplateView.as_view(
            template_name='students/dashboard.html',
        ),
        name='students_dashboard',
    ),
    path(
        'aluno/aulas/',
        TemplateView.as_view(
            template_name='students/aulas.html',
        ),
        name='students_lessons',
    ),
    path(
        'aluno/materiais/',
        students_views.materials,
        name='students_materials',
    ),
    path(
        'teachers/dashboard/',
        TemplateView.as_view(
            template_name='teachers/dashboard.html',
        ),
        name='teachers_dashboard',
    ),
    path(
        'gestao/',
        TemplateView.as_view(
            template_name='admin_panel/dashboard.html',
        ),
        name='gestao_dashboard',
    ),
    # rotas previamente adicionadas
    path(
        'students/login/',
        RedirectView.as_view(
            pattern_name='accounts:login',
            permanent=False,
        ),
    ),
    path(
        'teachers/login/',
        RedirectView.as_view(
            pattern_name='accounts:login',
            permanent=False,
        ),
    ),
    path(
        'sobre/',
        TemplateView.as_view(
            template_name='sobre.html',
        ),
        name='sobre',
    ),
    # ...existing url patterns...
]