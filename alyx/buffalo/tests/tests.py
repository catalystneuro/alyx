from datetime import datetime

from django.test.testcases import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from buffalo.models import BuffaloSubject, BuffaloSession, Task
from misc.models import Lab, LabMember


class SubjectSessionTestCase(TestCase):
    def setUp(self):
        self.lab = Lab.objects.create(name="testlab")
        self.user = LabMember.objects.create(username="test1", password="test1")
        self.subject = BuffaloSubject.objects.create(
            nickname="test",
            birth_date=("2018-01-01"),
            lab=self.lab,
            responsible_user=self.user,
        )
        self.superuser = get_user_model().objects.create_superuser(
            "test", "test", "test"
        )
        self.client.login(username="test", password="test")

    def test_load_homepage(self):
        response = self.client.get("")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context_data["app_list"][0].models), 1)
        self.assertEqual(len(response.context_data["app_list"][1].models), 16)

    def test_subject_exists(self):
        # Subject exists
        self.assertTrue(BuffaloSubject.objects.filter(nickname="test").exists())
        # list subjects
        response = self.client.get("/buffalo/buffalosession/")
        self.assertEqual(response.status_code, 200)
        # Subject daily Observation
        url = reverse("daily-observation", kwargs={"subject_id": self.subject.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_create_session(self):
        self.session = BuffaloSession.objects.create(
            name=datetime.today().isoformat(), subject=self.subject
        )
        url_session_details = reverse(
            "session-details", kwargs={"session_id": self.session.id}
        )
        response = self.client.get(url_session_details)
        self.assertEqual(response.status_code, 200)

    def test_create_tasktype(self):
        self.task_type = Task.objects.create(name="test_task")
        response = self.client.get("/buffalo/task/")
        self.assertEqual(response.status_code, 200)

    def tearDown(self):
        self.user.delete()
