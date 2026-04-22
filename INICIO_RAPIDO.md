# 🚀 INÍCIO RÁPIDO - WALK

## ⚡ Comandos para Iniciar

```bash
# 1. Entre no diretório
cd /home/ubuntu/walk

# 2. Ative o ambiente virtual
source venv/bin/activate

# 3. Inicie o servidor
python manage.py runserver 0.0.0.0:8000
```

## 🔑 Credenciais de Teste

### 👤 ADMINISTRADOR
- **Email**: admin@walk.com
- **Senha**: admin123
- **Acesso**: Dashboard administrativo completo

### 👨‍🏫 PROFESSORES
1. **Maria Silva** (Matemática)
   - Email: maria.silva@walk.com
   - Senha: prof123

2. **João Santos** (Física)
   - Email: joao.santos@walk.com
   - Senha: prof123

### 🎒 ALUNOS
1. **Pedro Oliveira** (Mat: 2026001)
   - Email: pedro.oliveira@email.com
   - Senha: aluno123

2. **Ana Costa** (Mat: 2026002)
   - Email: ana.costa@email.com
   - Senha: aluno123

3. **Lucas Ferreira** (Mat: 2026003)
   - Email: lucas.ferreira@email.com
   - Senha: aluno123

4. **Júlia Martins** (Mat: 2026004)
   - Email: julia.martins@email.com
   - Senha: aluno123

## 📚 Dados Populados no Sistema

✅ **4 Disciplinas criadas:**
- MAT101 - Matemática Básica (Prof. Maria Silva)
- MAT102 - Álgebra Linear (Prof. Maria Silva)
- FIS101 - Física I - Mecânica (Prof. João Santos)
- FIS102 - Física II - Termodinâmica (Prof. João Santos)

✅ **8 Matrículas realizadas:**
- Cada aluno está matriculado em 2 disciplinas

✅ **4 Aulas em vídeo cadastradas:**
- 2 aulas de Matemática
- 2 aulas de Física

✅ **4 Posts no blog publicados:**
- Bem-vindo ao WALK
- Dicas de Estudo para o ENEM
- Cronograma de Aulas do 1º Semestre
- Como se preparar para Física

## 🌐 URLs Principais

- **Home**: http://localhost:8000
- **Login**: http://localhost:8000/login
- **Blog**: http://localhost:8000/blog
- **Django Admin**: http://localhost:8000/admin

## 📁 Estrutura de Arquivos Importantes

```
sistema_walk_django/
├── README.md                    # Documentação completa
├── INICIO_RAPIDO.md            # Este arquivo
├── populate_db.py              # Script de população do BD
├── requirements.txt            # Dependências Python
├── .env.example                # Exemplo de variáveis de ambiente
├── manage.py                   # Comandos Django
├── db.sqlite3                  # Banco de dados (já populado)
│
├── config/                     # Configurações Django
│   ├── settings.py            # Configurações principais
│   └── urls.py                # URLs principais
│
├── accounts/                   # Autenticação
├── students/                   # Portal do Aluno
├── teachers/                   # Portal do Professor
├── admin_panel/                # Área Administrativa
├── courses/                    # Disciplinas e Matrículas
├── materials/                  # Materiais e Vídeos
├── blog/                       # Blog
│
└── templates/                  # Templates HTML
    ├── accounts/
    ├── students/
    ├── teachers/
    ├── admin_panel/
    ├── blog/
    └── includes/
```

## 🛠 Comandos Úteis

```bash
# Criar novo superusuário
python manage.py createsuperuser

# Popular banco novamente (opcional)
python populate_db.py

# Verificar problemas
python manage.py check

# Executar shell
python manage.py shell

# Coletar arquivos estáticos
python manage.py collectstatic
```

## 🎯 Próximos Passos

1. **Explore o sistema** com as credenciais fornecidas
2. **Adicione novos materiais** como professor
3. **Teste o fluxo completo** de cada tipo de usuário
4. **Configure para produção** seguindo o README.md
5. **Faça deploy** em Render, Railway ou Heroku

## 💡 Dicas

- Use o Django Admin (http://localhost:8000/admin) para gerenciamento avançado
- Todas as senhas de teste são fáceis de lembrar para desenvolvimento
- O banco de dados SQLite já está populado e pronto para uso
- Para resetar o banco: delete `db.sqlite3` e execute as migrations novamente

## 📞 Suporte

Consulte o README.md para documentação completa e instruções de deploy.

---

**WALK - Educação de qualidade para todos! 🎓**
