# 🎓 WALK - Plataforma de Gestão para Cursinhos Populares

[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Ready-blue.svg)](https://www.postgresql.org/)

Sistema completo de gestão educacional desenvolvido em Django para cursinhos populares, com **3 portais distintos**: Aluno, Professor e Administrativo.

## 📋 Índice

- [Funcionalidades](#-funcionalidades)
- [Tecnologias](#-tecnologias)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Instalação Local](#-instalação-local)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Deploy](#-deploy)
- [Credenciais Padrão](#-credenciais-padrão)

## ✨ Funcionalidades

### 🎒 Portal do Aluno
- Visualização de disciplinas matriculadas
- Acesso a materiais de estudo (PDFs, documentos)
- Acesso a aulas gravadas (links YouTube/Vimeo)
- Blog com conteúdos preparatórios
- Dashboard personalizado

### 👨‍🏫 Portal do Professor
- Gerenciamento de disciplinas
- Upload de materiais didáticos
- Cadastro de links para aulas gravadas
- Visualização de alunos matriculados
- Dashboard com estatísticas

### ⚙️ Área Administrativa
- CRUD completo de alunos
- CRUD completo de professores
- Gerenciamento de disciplinas
- Sistema de matrículas (vincular aluno-disciplina)
- Gerenciamento de blog (notícias, avisos)
- Dashboard com estatísticas gerais
- Django Admin integrado

## 🛠 Tecnologias

- **Framework**: Django 5.2
- **Linguagem**: Python 3.11+
- **Banco de Dados**: PostgreSQL (produção) / SQLite (desenvolvimento)
- **Frontend**: Bootstrap 5, Bootstrap Icons
- **Processamento de Imagens**: Pillow
- **Gerenciamento de Variáveis**: python-decouple
- **Servidor de Produção**: Gunicorn
- **Arquivos Estáticos**: Whitenoise

## 📁 Estrutura do Projeto

```
sistema_walk_django/
├── accounts/              # Autenticação e usuários
├── students/              # Portal do aluno
├── teachers/              # Portal do professor
├── admin_panel/           # Área administrativa
├── courses/               # Disciplinas e matrículas
├── materials/             # Materiais e vídeo-aulas
├── blog/                  # Blog de notícias
├── config/                # Configurações Django
├── templates/             # Templates HTML
│   ├── accounts/
│   ├── students/
│   ├── teachers/
│   ├── admin_panel/
│   ├── blog/
│   └── includes/
├── static/                # Arquivos estáticos
├── media/                 # Uploads (materiais, fotos)
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Instalação Local

### Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Git
- PostgreSQL (opcional para produção)

### Passo a Passo

1. **Clone o repositório**
```bash
git clone <seu-repositorio>
cd sistema_walk_django
```

2. **Crie e ative o ambiente virtual**

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. **Execute as migrações**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Crie um superusuário**
```bash
python manage.py createsuperuser
```
- Email: admin@walk.com
- Username: admin
- Password: (escolha uma senha segura)
- Tipo de usuário: ADMIN

7. **Colete os arquivos estáticos**
```bash
python manage.py collectstatic --noinput
```

8. **Execute o servidor de desenvolvimento**
```bash
python manage.py runserver
```

9. **Acesse o sistema**
- Aplicação: http://localhost:8000
- Django Admin: http://localhost:8000/admin

## ⚙️ Configuração

### Arquivo .env

Copie o arquivo `.env.example` para `.env` e configure:

```env
# Django
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de Dados
USE_SQLITE=True  # True para SQLite, False para PostgreSQL

# PostgreSQL (se USE_SQLITE=False)
DB_NAME=walk_db
DB_USER=postgres
DB_PASSWORD=sua-senha
DB_HOST=localhost
DB_PORT=5432
```

### Configuração do PostgreSQL

1. **Instale o PostgreSQL**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. **Crie o banco de dados**
```bash
sudo -u postgres psql
CREATE DATABASE walk_db;
CREATE USER walk_user WITH PASSWORD 'sua_senha';
ALTER ROLE walk_user SET client_encoding TO 'utf8';
ALTER ROLE walk_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE walk_user SET timezone TO 'America/Sao_Paulo';
GRANT ALL PRIVILEGES ON DATABASE walk_db TO walk_user;
\q
```

3. **Configure o .env**
```env
USE_SQLITE=False
DB_NAME=walk_db
DB_USER=walk_user
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
```

## 📖 Uso

### Criar Usuários de Teste

```bash
# Execute o shell do Django
python manage.py shell

# No shell Python:
from accounts.models import User
from students.models import Student
from teachers.models import Teacher

# Criar um aluno
aluno_user = User.objects.create_user(
    username='aluno1',
    email='aluno@teste.com',
    password='senha123',
    first_name='João',
    last_name='Silva',
    user_type='ALUNO'
)
Student.objects.create(user=aluno_user, enrollment_number='2026001')

# Criar um professor
prof_user = User.objects.create_user(
    username='prof1',
    email='prof@teste.com',
    password='senha123',
    first_name='Maria',
    last_name='Santos',
    user_type='PROFESSOR'
)
Teacher.objects.create(user=prof_user, specialization='Matemática')
```

### Fluxo de Uso

1. **Login**: Acesse http://localhost:8000/login
2. **Dashboard**: Será redirecionado automaticamente baseado no tipo de usuário
3. **Portal do Aluno**: Visualize disciplinas, materiais e aulas
4. **Portal do Professor**: Gerencie suas disciplinas e faça upload de conteúdo
5. **Área Administrativa**: Gerencie todo o sistema

## 🌐 Deploy

### Deploy no Render

1. **Crie uma conta no Render** (https://render.com)

2. **Crie um novo PostgreSQL Database**
   - Nome: walk-db
   - Copie as credenciais

3. **Crie um novo Web Service**
   - Conecte ao seu repositório GitHub
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - Start Command: `gunicorn walk.wsgi:application`

4. **Configure as variáveis de ambiente no Render**
```
SECRET_KEY=<gere-uma-chave-secreta-forte>
DEBUG=False
ALLOWED_HOSTS=seu-app.onrender.com
USE_SQLITE=False
DB_NAME=<do-render-postgres>
DB_USER=<do-render-postgres>
DB_PASSWORD=<do-render-postgres>
DB_HOST=<do-render-postgres>
DB_PORT=5432
```

### Deploy no Railway

1. **Crie uma conta no Railway** (https://railway.app)

2. **Crie um novo projeto**
   - Add PostgreSQL
   - Add GitHub Repo

3. **Configure as variáveis de ambiente**
```
SECRET_KEY=<gere-uma-chave-secreta>
DEBUG=False
ALLOWED_HOSTS=${{RAILWAY_STATIC_URL}}
USE_SQLITE=False
DB_NAME=${{PGDATABASE}}
DB_USER=${{PGUSER}}
DB_PASSWORD=${{PGPASSWORD}}
DB_HOST=${{PGHOST}}
DB_PORT=${{PGPORT}}
```

4. **Deploy automático** será feito a cada push

### Deploy no Heroku

1. **Instale o Heroku CLI**

2. **Crie um app**
```bash
heroku create walk
```

3. **Adicione PostgreSQL**
```bash
heroku addons:create heroku-postgresql:mini
```

4. **Configure variáveis**
```bash
heroku config:set SECRET_KEY='sua-chave'
heroku config:set DEBUG=False
heroku config:set USE_SQLITE=False
```

5. **Crie o Procfile**
```
web: gunicorn walk.wsgi:application
release: python manage.py migrate --noinput
```

6. **Deploy**
```bash
git push heroku main
```

## 🔑 Credenciais Padrão

Após criar o superusuário, você pode criar usuários de teste:

**Administrador:**
- Email: admin@walk.com
- Senha: (definida por você no createsuperuser)

**Professor (exemplo):**
- Email: professor@walk.com
- Senha: prof123456

**Aluno (exemplo):**
- Email: aluno@walk.com
- Senha: aluno123456

## 🎨 Cores do Sistema

- **Primária**: #0056b3 (Azul Escuro)
- **Secundária**: #007bff (Azul)
- **Fundo**: #f8f9fa (Cinza Claro)
- **Texto**: #333333 (Cinza Escuro)

## 📝 Comandos Úteis

```bash
# Criar migrações
python manage.py makemigrations

# Aplicar migrações
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Coletar arquivos estáticos
python manage.py collectstatic

# Executar servidor
python manage.py runserver

# Shell interativo
python manage.py shell

# Verificar problemas
python manage.py check
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## 📄 Licença

Este projeto é de código aberto e está disponível para uso educacional.

## 📧 Suporte

Para dúvidas e suporte, entre em contato através do email: suporte@walk.com

---

**Desenvolvido para cursinhos populares - Educação de qualidade para todos! 🎓**
