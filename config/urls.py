"""
URL configuration for WALK project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from admin_panel import views as admin_panel_views
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # (as rotas de login específicas estão em accounts.urls)

    # Accounts (autenticação e home)
    path('', include('accounts.urls')),

    # Portal do Aluno (raiz redireciona para /aluno/dashboard/)
    path(
        'aluno/',
        RedirectView.as_view(
            url='/aluno/dashboard/',
            permanent=False,
        ),
    ),
    path('aluno/', include('students.urls')),

    # Portal do Professor
    path('professor/', include('teachers.urls')),

    # Rota raiz do Painel (evita 404 em /painel/)
    path('painel/', admin_panel_views.dashboard, name='admin_panel_root'),

    # Área Administrativa
    path('painel/', include('admin_panel.urls')),

    # Blog
    path('blog/', include('blog.urls')),

    # Questionários
    path('questionarios/', include('assessments.urls')),

    # Home
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]

# Servir arquivos de media em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )

# Customização do Django Admin
admin.site.site_header = (
    "WALK - Administração"
)
admin.site.site_title = (
    "WALK Admin"
)
admin.site.index_title = (
    "Bem-vindo ao painel administrativo"
)

# Removido: bloco de deduplicação de /professor/.
# Se houver mais de um include de teachers, mantenha apenas um manualmente.
