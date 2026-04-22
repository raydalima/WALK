#!/usr/bin/env python
"""
Script para popular o banco de dados com dados de teste
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# imports de modelos devem ocorrer após django.setup()
from accounts.models import User  # noqa: E402
from students.models import Student  # noqa: E402
from teachers.models import Teacher  # noqa: E402
from courses.models import Course, Enrollment  # noqa: E402
from materials.models import VideoLesson  # noqa: E402
from blog.models import BlogPost  # noqa: E402


def create_users():
    """Criar usuários de teste"""
    print("Criando usuários...")

    # Professores
    if not User.objects.filter(email='maria.silva@walk.com').exists():
        prof1_user = User.objects.create_user(
            username='maria_silva',
            email='maria.silva@walk.com',
            password='prof123',
            first_name='Maria',
            last_name='Silva',
            user_type='PROFESSOR',
        )
        Teacher.objects.create(
            user=prof1_user,
            specialization='Matemática',
            bio='Professora de matemática com 15 anos de experiência',
            experience_years=15,
        )
        print('✓ Professora Maria Silva criada')

    if not User.objects.filter(email='joao.santos@walk.com').exists():
        prof2_user = User.objects.create_user(
            username='joao_santos',
            email='joao.santos@walk.com',
            password='prof123',
            first_name='João',
            last_name='Santos',
            user_type='PROFESSOR',
        )
        Teacher.objects.create(
            user=prof2_user,
            specialization='Física',
            bio='Professor de física especializado em vestibulares',
            experience_years=10,
        )
        print('✓ Professor João Santos criado')

    # Alunos
    alunos_data = [
        (
            'pedro.oliveira',
            'Pedro',
            'Oliveira',
            'pedro.oliveira@email.com',
            '2026001',
        ),
        (
            'ana.costa',
            'Ana',
            'Costa',
            'ana.costa@email.com',
            '2026002',
        ),
        (
            'lucas.ferreira',
            'Lucas',
            'Ferreira',
            'lucas.ferreira@email.com',
            '2026003',
        ),
        (
            'julia.martins',
            'Júlia',
            'Martins',
            'julia.martins@email.com',
            '2026004',
        ),
    ]

    for username, first_name, last_name, email, enrollment in alunos_data:
        if not User.objects.filter(email=email).exists():
            aluno_user = User.objects.create_user(
                username=username,
                email=email,
                password='aluno123',
                first_name=first_name,
                last_name=last_name,
                user_type='ALUNO',
            )
            Student.objects.create(
                user=aluno_user,
                enrollment_number=enrollment,
                city='São Paulo',
                state='SP',
            )
            print(f'✓ Aluno {first_name} {last_name} criado')


def create_courses():
    """Criar disciplinas"""
    print('\nCriando disciplinas...')

    maria = Teacher.objects.filter(
        user__email='maria.silva@walk.com'
    ).first()
    joao = Teacher.objects.filter(
        user__email='joao.santos@walk.com'
    ).first()

    if not maria or not joao:
        print('⚠ Professores não encontrados. Execute create_users().')
        return

    courses_data = [
        ('MAT101', 'Matemática Básica', maria, 60, '1º Semestre'),
        ('MAT102', 'Álgebra Linear', maria, 60, '1º Semestre'),
        ('FIS101', 'Física I - Mecânica', joao, 60, '1º Semestre'),
        ('FIS102', 'Física II - Termodinâmica', joao, 60, '2º Semestre'),
    ]

    for code, name, teacher, workload, semester in courses_data:
        if not Course.objects.filter(code=code, year=2026).exists():
            Course.objects.create(
                code=code,
                name=name,
                description=(
                    f'Disciplina de {name} para preparação vestibular'
                ),
                teacher=teacher,
                workload=workload,
                semester=semester,
                year=2026,
            )
            print(f'✓ Disciplina {code} - {name} criada')


def create_enrollments():
    """Criar matrículas"""
    print('\nCriando matrículas...')

    students = Student.objects.all()
    courses = Course.objects.all()

    if not students.exists() or not courses.exists():
        print('⚠ Alunos ou disciplinas não encontrados.')
        return

    count = 0
    for student in students:
        for course in courses[:2]:  # Matricular cada aluno em 2 disciplinas
            exists_qs = Enrollment.objects.filter(
                student=student, course=course
            ).exists()
            if not exists_qs:
                Enrollment.objects.create(student=student, course=course)
                count += 1

    print(f'✓ {count} matrículas criadas')


def create_video_lessons():
    """Criar aulas em vídeo"""
    print('\nCriando aulas em vídeo...')

    mat101 = Course.objects.filter(code='MAT101').first()
    fis101 = Course.objects.filter(code='FIS101').first()

    if not mat101 or not fis101:
        print('⚠ Disciplinas não encontradas.')
        return

    maria = Teacher.objects.filter(
        user__email='maria.silva@walk.com'
    ).first()
    joao = Teacher.objects.filter(
        user__email='joao.santos@walk.com'
    ).first()

    videos = [
        (
            mat101,
            maria.user,
            'Introdução aos Números',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            1,
            '45 minutos',
        ),
        (
            mat101,
            maria.user,
            'Operações Básicas',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            2,
            '50 minutos',
        ),
        (
            fis101,
            joao.user,
            'Cinemática - Parte 1',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            1,
            '60 minutos',
        ),
        (
            fis101,
            joao.user,
            'Dinâmica - Leis de Newton',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            2,
            '55 minutos',
        ),
    ]

    count = 0
    for course, uploaded_by, title, url, lesson_num, duration in videos:
        exists_video = VideoLesson.objects.filter(
            course=course, lesson_number=lesson_num
        ).exists()
        if not exists_video:
            VideoLesson.objects.create(
                course=course,
                uploaded_by=uploaded_by,
                title=title,
                description=(
                    f'Aula sobre {title}'
                ),
                video_url=url,
                platform='YOUTUBE',
                lesson_number=lesson_num,
                duration=duration,
            )
            count += 1

    print(f'✓ {count} aulas em vídeo criadas')


def create_blog_posts():
    """Criar posts no blog"""
    print('\nCriando posts no blog...')

    admin = User.objects.filter(email='admin@walk.com').first()
    if not admin:
        print('⚠ Usuário admin não encontrado.')
        return

    posts = [
        (
            'Bem-vindo ao WALK',
            'ANNOUNCEMENT',
            'Apresentamos nossa nova plataforma de gestão educacional.',
        ),
        (
            'Dicas de Estudo para o ENEM',
            'TIP',
            'Melhores dicas para se preparar para o ENEM 2026.',
        ),
        (
            'Cronograma de Aulas do 1º Semestre',
            'NEWS',
            'Cronograma de aulas do primeiro semestre de 2026.',
        ),
        (
            'Como se preparar para Física',
            'CONTENT',
            'Guia prático para estudar física de forma eficiente.',
        ),
    ]

    count = 0
    for title, category, excerpt in posts:
        if not BlogPost.objects.filter(title=title).exists():
            BlogPost.objects.create(
                title=title,
                category=category,
                content=(
                    f'{excerpt}\n\n'
                    'Conteúdo completo do post com informações '
                    'detalhadas para os estudantes do cursinho popular.'
                ),
                excerpt=excerpt,
                author=admin,
                is_published=True,
            )
            count += 1

    print(f'✓ {count} posts no blog criados')


def main():
    """Executar todas as funções"""
    print('=' * 60)
    print('POPULANDO BANCO DE DADOS COM DADOS DE TESTE')
    print('=' * 60)

    create_users()
    create_courses()
    create_enrollments()
    create_video_lessons()
    create_blog_posts()

    print('\n' + '=' * 60)
    print('✅ BANCO DE DADOS POPULADO COM SUCESSO!')
    print('=' * 60)
    print('\n📝 CREDENCIAIS DE TESTE:')
    print('\n👤 ADMINISTRADOR:')
    print('   Email: admin@walk.com')
    print('   Senha: admin123')
    print('\n👨‍🏫 PROFESSORES:')
    print('   Email: maria.silva@walk.com | Senha: prof123')
    print('   Email: joao.santos@walk.com | Senha: prof123')
    print('\n🎒 ALUNOS:')
    print('   Email: pedro.oliveira@email.com | Senha: aluno123')
    print('   Email: ana.costa@email.com | Senha: aluno123')
    print('   Email: lucas.ferreira@email.com | Senha: aluno123')
    print('   Email: julia.martins@email.com | Senha: aluno123')
    print('\n🚀 Acesse: http://localhost:8000')
    print('=' * 60)


if __name__ == '__main__':
    main()
