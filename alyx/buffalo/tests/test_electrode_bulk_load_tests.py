import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from buffalo.models import BuffaloSubject, Electrode, Device

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class BulkLoadTests(TestCase):
    def setUp(self):
        User = get_user_model()
        my_admin = User.objects.create_superuser("admin", "admin@test.com", "123456")
        self.client = Client()
        self.client.force_login(my_admin)

        horacio = BuffaloSubject.objects.get_or_create(nickname="Horacio")[0]
        spock = BuffaloSubject.objects.get_or_create(nickname="Spock")[0]

        Device.objects.get_or_create(name="posterior-horacio", subject=horacio)
        Device.objects.get_or_create(name="posterior-spock", subject=spock)

        # Open file
        self.file_spock_mat = open(
            os.path.join(TEST_DIR + "/files", "SpockTrodeInfo.mat"), "rb"
        )
        self.file_spock_stl = open(
            os.path.join(TEST_DIR + "/files", "Spock_HPC.stl"), "rb"
        )

    def test_upload_for_another_subject(self):
        dhoracio = Device.objects.get(name="posterior-horacio")
        bulk_load_url = reverse(
            "electrode-bulk-load", kwargs={"device_id": dhoracio.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {"file": self.file_spock_mat, "device": dhoracio.id},
            format="multipart",
        )
        self.assertContains(resp, "It cannot find an structure called: Horacio")

    def test_upload_for_another_subject_using_text_field(self):
        dhoracio = Device.objects.get(name="posterior-horacio")
        bulk_load_url = reverse(
            "electrode-bulk-load", kwargs={"device_id": dhoracio.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_spock_mat,
                "device": dhoracio.id,
                "structure_name": "Spock",
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(resp, "File loaded successful")

    def test_upload_bad_file_extension(self):
        dhoracio = Device.objects.get(name="posterior-horacio")
        bulk_load_url = reverse(
            "electrode-bulk-load", kwargs={"device_id": dhoracio.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_spock_stl,
                "subject": dhoracio.id,
                "structure_name": "Spock",
            },
            format="multipart",
        )
        self.assertContains(resp, "File extension “stl” is not allowed")

    def test_upload_well(self):
        dspock = Device.objects.get(name="posterior-spock")
        bulk_load_url = reverse("electrode-bulk-load", kwargs={"device_id": dspock.id})
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_spock_mat,
                "device": dspock.id,
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(resp, "File loaded successful")
        electrodes = Electrode.objects.filter(device=dspock.id)
        self.assertEquals(124, len(electrodes))
