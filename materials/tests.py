from django.test import TestCase

from accounts.models import User
from courses.models import AreaConhecimento, Disciplina
from materials.models import Material, VideoLesson


class MaterialModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='prof1',
            email='prof1@example.com',
            password='senha-segura-123',
            user_type=User.UserType.PROFESSOR,
        )
        self.area = AreaConhecimento.objects.create(nome='REDACAO')
        self.course = Disciplina.objects.create(
            area=self.area,
            nome='Oficina de Texto',
        )

    def test_material_string_uses_course_name(self):
        material = Material(
            title='Lista 01',
            course=self.course,
            uploaded_by=self.user,
            external_url='https://drive.google.com/file/d/exemplo/view',
        )

        self.assertIn('Oficina de Texto', str(material))

    def test_video_string_uses_course_name(self):
        video = VideoLesson(
            title='Aula 01',
            course=self.course,
            uploaded_by=self.user,
            video_url='https://youtu.be/exemplo',
        )

        self.assertIn('Oficina de Texto', str(video))
