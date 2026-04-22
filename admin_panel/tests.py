from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from accounts.models import User
from courses.models import AreaConhecimento, Disciplina, Enrollment
from admin_panel.models import EmailCommunication
from students.models import PreRegistration, Student
from teachers.models import Teacher


class AdminEnrollmentReportTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='senha-segura-123',
            user_type=User.UserType.ADMIN,
            is_staff=True,
        )
        student_user = User.objects.create_user(
            username='alunoadmin',
            email='alunoadmin@example.com',
            password='senha-segura-123',
            user_type=User.UserType.ALUNO,
            first_name='Aluno',
            last_name='Teste',
        )
        self.student = Student.objects.create(
            user=student_user,
            enrollment_number='2026009',
            cpf='123.456.789-00',
        )
        area = AreaConhecimento.objects.create(nome='MATEMATICA')
        course = Disciplina.objects.create(area=area, nome='Matematica Basica')
        Enrollment.objects.create(student=self.student, course=course)

    def test_general_enrollment_report_loads(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_panel:relatorio_alunos_geral'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Aluno Teste')
        self.assertContains(response, 'Matematica Basica')

    def test_general_enrollment_report_pdf_downloads(self):
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse('admin_panel:relatorio_alunos_geral_pdf'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_enrollment_create_from_pre_registration_creates_user_student_and_enrollment(self):
        self.client.force_login(self.admin_user)
        area = AreaConhecimento.objects.create(nome='LINGUAGENS')
        course = Disciplina.objects.create(area=area, nome='Redacao ENEM')
        preregistration = PreRegistration.objects.create(
            name='Maria da Silva',
            email='maria.pre@example.com',
            phone='94999999999',
            cpf='12345678901',
            address='Rua das Flores, 123',
            city='Maraba',
            state='PA',
            zip_code='68500-000',
            responsible_name='Ana da Silva',
            responsible_phone='94988888888',
            consent=True,
        )

        response = self.client.post(
            reverse('admin_panel:matricula_create'),
            data={
                'first_name': '',
                'last_name': '',
                'birth_date': '',
                'gender': '',
                'cpf': '',
                'rg': '',
                'social_name': '',
                'pronouns': '',
                'phone': '',
                'email': '',
                'responsible_name': '',
                'responsible_phone': '',
                'responsible_email': '',
                'previous_school': '',
                'previous_grade': '',
                'graduation_year': '',
                'emergency_contact_name': '',
                'emergency_contact_phone': '',
                'emergency_contact_relation': '',
                'address': '',
                'city': '',
                'state': '',
                'zip_code': '',
                'pre_registration': preregistration.id,
                'course': course.id,
                'turma': '',
                'is_active': 'on',
                'notes': 'Matrícula criada a partir do pré-cadastro.',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            User.objects.filter(email='maria.pre@example.com', user_type=User.UserType.ALUNO).exists()
        )
        created_user = User.objects.get(email='maria.pre@example.com')
        created_student = Student.objects.get(user=created_user)
        self.assertEqual(created_student.cpf, '12345678901')
        self.assertEqual(created_student.city, 'Maraba')
        self.assertTrue(
            Enrollment.objects.filter(student=created_student, course=course).exists()
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_admin_can_send_individual_email_to_student(self):
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('admin_panel:email_individual_create'),
            data={
                'recipient_group': EmailCommunication.RecipientGroup.ALUNO,
                'student': self.student.id,
                'teacher': '',
                'subject': 'Aviso de aula',
                'message': 'Hoje teremos revisão.',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        communication = EmailCommunication.objects.get(subject='Aviso de aula')
        self.assertEqual(communication.successful_recipients, 1)
        self.assertEqual(communication.recipients.first().email, self.student.user.email)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_admin_can_send_email_to_responsible(self):
        self.student.responsible_name = 'Responsável Teste'
        self.student.responsible_email = 'responsavel@example.com'
        self.student.save()
        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('admin_panel:email_individual_create'),
            data={
                'recipient_group': EmailCommunication.RecipientGroup.RESPONSAVEL,
                'student': self.student.id,
                'teacher': '',
                'subject': 'Comunicado ao responsável',
                'message': 'Favor acompanhar a frequência.',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        communication = EmailCommunication.objects.get(subject='Comunicado ao responsável')
        self.assertEqual(communication.recipients.first().email, 'responsavel@example.com')

    def test_teacher_cannot_access_email_module(self):
        teacher_user = User.objects.create_user(
            username='prof_email',
            email='prof_email@example.com',
            password='senha-segura-123',
            user_type=User.UserType.PROFESSOR,
        )
        Teacher.objects.create(user=teacher_user)
        self.client.force_login(teacher_user)
        response = self.client.get(reverse('admin_panel:email_communications_list'))

        self.assertEqual(response.status_code, 302)
