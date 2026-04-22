Documentação do WALK
===========================

Visão geral
----------
WALK é um projeto Django modular com os seguintes apps principais:

- accounts: autenticação, modelo de usuário customizado e permissões.
- students: painel do aluno, visualizações, relatórios (exportar DOC/PDF) e URLs.
- teachers: modelos/perfis de professores.
- courses: modelos de áreas, disciplinas e matrículas (compatibilidade Course/Disciplina).
- materials: materiais e VideoLesson.
- blog: posts e CMS simples.
- admin_panel: views para administração personalizada.

Estrutura e arquivos principais
-------------------------------
config/
- settings.py: configurações do Django (base, banco, apps, middleware, URLs, static/media).
- urls.py: roteamento principal; inclui rotas de apps e rotas explícitas de exportação.

accounts/
- models.py: modelo User customizado (AUTH_USER_MODEL definido em settings).
- urls.py, views.py, forms.py: endpoints de login, logout e gerenciamento de perfis.
- decorators.py: decoradores como student_required, admin_required usados nas views.

students/
- models.py: modelos relacionados ao perfil do aluno.
- views.py: views de front (dashboard, my_courses, course_detail, materials_list, video_lessons_list).
  - materials_list aceita opcionalmente course_id para listar materiais de uma disciplina específica.
- views_reports.py: funções auxiliares e endpoints para exportar listas de matrícula em DOCX e PDF.
- urls.py: rotas do portal do aluno (inclui aliases compatíveis como view_materials).

courses/
- models.py: AreaConhecimento, Disciplina (alias Course), Enrollment. `Course = Disciplina` para compat.
- admin.py: registro seguro das models no Django Admin.
- migrations/: migrações do app (0001_initial e demais; atenção ao histórico de merges se houver).

materials/
- models.py: Material e VideoLesson vinculados a uma disciplina/curso.

admin_panel/
- views.py: funcionalidades administrativas (lista de alunos, professores, cursos, matrículas, posts).

blog/
- models.py e views: posts do blog, listagem e gerenciamento.

Como gerar a documentação em PDF (localmente)
--------------------------------------------
Pré-requisitos (no ambiente virtual):

```bash
pip install markdown2 weasyprint
```

Uso do script:

```bash
python scripts/generate_docs_pdf.py docs/system_documentation.md docs/system_documentation.pdf
```

O script converte o Markdown em HTML e usa WeasyPrint para gerar o PDF. Se preferir, abra o Markdown em um editor (VSCode) ou gere o PDF com outra ferramenta.

Notas importantes
-----------------
- Migrações: sempre versionar a pasta migrations; se o banco e as migrações estiverem fora de sincronia, faça backup do db.sqlite3 e das migrations antes de ações destrutivas.
- Rotas/compatibilidade: o projeto inclui aliases e compatibilidades (por ex., Course <-> Disciplina, nomes de rotas antigos) para evitar NoReverseMatch após renomeações.
- Exportação DOCX/PDF: depende de python-docx e WeasyPrint; endpoints em students/views_reports.py verificam dependências e retornam 500 com instruções se ausentes.

Seção rápida de troubleshooting
------------------------------
- Erro "no such table": rodar `python manage.py makemigrations` e `python manage.py migrate` ou usar `--fake` com cautela.
- NoReverseMatch para nomes de rotas: verifique students/urls.py e templates que fazem {% url 'students:view_materials' course.id %}.
- Permissões: use admin_panel rotas protegidas por admin_required; verifique User.user_type.

Fim da documentação.
