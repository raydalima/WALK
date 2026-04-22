from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from courses.models import AreaConhecimento, Disciplina, Enrollment, Turma, TurmaEnrollment
from assessments.models import Activity, ActivityResult, EssaySubmission, Quiz
from students.models import Student


class StudentPortalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='aluno1',
            email='aluno1@example.com',
            password='senha-segura-123',
            user_type=User.UserType.ALUNO,
        )
        self.student = Student.objects.create(
            user=self.user,
            enrollment_number='2026001',
        )
        self.area = AreaConhecimento.objects.create(nome='LINGUAGENS')
        self.course = Disciplina.objects.create(
            area=self.area,
            nome='Redacao',
            descricao='Praticas de escrita',
        )
        Enrollment.objects.create(student=self.student, course=self.course)

    def test_my_courses_page_loads(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('students:my_courses'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Redacao')

    def test_course_list_page_uses_courses_app(self):
        response = self.client.get(reverse('students:course_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Redacao')

    def test_student_quiz_list_shows_only_enrolled_course_quizzes(self):
        other_course = Disciplina.objects.create(
            area=self.area,
            nome='Matematica',
            descricao='Exercicios de matematica',
        )
        Quiz.objects.create(
            course=self.course,
            title='Simulado de Redacao',
            created_by=self.user,
            is_published=True,
        )
        Quiz.objects.create(
            course=other_course,
            title='Simulado de Matematica',
            created_by=self.user,
            is_published=True,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('assessments:student_quiz_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Simulado de Redacao')
        self.assertNotContains(response, 'Simulado de Matematica')

    def test_student_can_submit_essay(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse('students:essay_submit'),
            data={
                'course': self.course.id,
                'title': 'Redação ENEM',
                'prompt': 'Os desafios da educação no Brasil',
                'submission_url': 'https://docs.google.com/document/d/redacao/edit',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            EssaySubmission.objects.filter(
                student=self.student,
                course=self.course,
                title='Redação ENEM',
            ).exists()
        )

    def test_student_can_submit_activity_link(self):
        turma = Turma.objects.create(nome='Turma ENEM', ano=2026)
        turma.disciplines.add(self.course)
        TurmaEnrollment.objects.create(student=self.student, turma=turma)
        activity = Activity.objects.create(
            title='Atividade de interpretação',
            turma=turma,
            course=self.course,
            area=self.area,
            created_by=self.user,
            status=Activity.Status.PUBLICADA,
        )

        self.client.force_login(self.user)
        response = self.client.post(
            reverse('students:activity_submit', args=[activity.id]),
            data={
                'submission_url': 'https://docs.google.com/document/d/atividade/edit',
                'notes': 'Segue atividade.',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        result = ActivityResult.objects.get(activity=activity, student=self.student)
        self.assertEqual(result.status, ActivityResult.Status.ENVIADA)
        self.assertEqual(
            result.submission_url,
            'https://docs.google.com/document/d/atividade/edit',
        )
