from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from attendance.models import AttendanceRecord, AttendanceSession
from assessments.models import Activity, ActivityResult, EssaySubmission
from courses.models import AreaConhecimento, Disciplina, Enrollment, Turma, TurmaEnrollment
from students.models import Student
from teachers.models import Teacher


class TeacherPortalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='professor1',
            email='professor1@example.com',
            password='senha-segura-123',
            user_type=User.UserType.PROFESSOR,
        )
        self.teacher = Teacher.objects.create(user=self.user, specialization='Linguagens')
        self.area = AreaConhecimento.objects.create(nome='HUMANAS')
        Disciplina.objects.create(area=self.area, nome='Historia')

    def test_dashboard_loads_for_teacher(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('teachers:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Historia')

    def test_attendance_session_pdf_downloads(self):
        self.client.force_login(self.user)
        course = Disciplina.objects.get(nome='Historia')
        student_user = User.objects.create_user(
            username='aluno_pdf',
            email='aluno_pdf@example.com',
            password='senha-segura-123',
            user_type=User.UserType.ALUNO,
            first_name='Aluno',
            last_name='PDF',
        )
        student = Student.objects.create(user=student_user)
        Enrollment.objects.create(student=student, course=course)
        session = AttendanceSession.objects.create(
            course=course,
            teacher=self.user,
            created_by=self.user,
            date='2026-04-20',
            content_taught='Revisao geral',
        )
        AttendanceRecord.objects.create(
            session=session,
            student=student,
            status=AttendanceRecord.Status.PRESENT,
            marked_by=self.user,
        )

        response = self.client.get(
            reverse('teachers:attendance_session_pdf', args=[session.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_teacher_can_open_corrections_home_with_essay(self):
        self.client.force_login(self.user)
        course = Disciplina.objects.get(nome='Historia')
        student_user = User.objects.create_user(
            username='aluno_redacao',
            email='aluno_redacao@example.com',
            password='senha-segura-123',
            user_type=User.UserType.ALUNO,
            first_name='Aluno',
            last_name='Redacao',
        )
        student = Student.objects.create(user=student_user)
        Enrollment.objects.create(student=student, course=course)
        EssaySubmission.objects.create(
            student=student,
            course=course,
            title='Redação teste',
            submission_url='https://docs.google.com/document/d/redacao/edit',
        )

        response = self.client.get(reverse('teachers:corrections_home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Redação teste')

    def test_teacher_can_correct_activity_submission(self):
        self.client.force_login(self.user)
        course = Disciplina.objects.get(nome='Historia')
        turma = Turma.objects.create(nome='Turma Humanas', ano=2026)
        turma.disciplines.add(course)
        turma.teachers.add(self.teacher)
        student_user = User.objects.create_user(
            username='aluno_atividade',
            email='aluno_atividade@example.com',
            password='senha-segura-123',
            user_type=User.UserType.ALUNO,
            first_name='Aluno',
            last_name='Atividade',
        )
        student = Student.objects.create(user=student_user)
        TurmaEnrollment.objects.create(student=student, turma=turma)
        activity = Activity.objects.create(
            title='Resumo sobre Brasil Colônia',
            turma=turma,
            course=course,
            area=self.area,
            teacher=self.user,
            created_by=self.user,
            status=Activity.Status.PUBLICADA,
        )
        ActivityResult.objects.create(
            activity=activity,
            student=student,
            status=ActivityResult.Status.ENVIADA,
            submission_url='https://docs.google.com/document/d/atividade/edit',
        )

        response = self.client.post(
            reverse('teachers:activity_result_update', args=[activity.id, student.id]),
            data={
                'status': ActivityResult.Status.CORRIGIDA,
                'teacher_feedback': 'Bom desenvolvimento.',
                'score': '9.5',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        result = ActivityResult.objects.get(activity=activity, student=student)
        self.assertEqual(result.status, ActivityResult.Status.CORRIGIDA)
        self.assertEqual(result.corrected_by, self.user)
        self.assertEqual(result.teacher_feedback, 'Bom desenvolvimento.')
