import os
import tempfile
import shutil
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from buffalo.models import BuffaloSubject, STLFile


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class STLUploadTests(TestCase):
    def setUp(self):
        User = get_user_model()
        my_admin = User.objects.create_superuser("admin", "admin@test.com", "123456")
        self.client = Client()
        self.client.force_login(my_admin)

        BuffaloSubject.objects.get_or_create(nickname="Spock")

        # Open file
        self.file_spock_mat = open(
            os.path.join(TEST_DIR + "/files", "SpockTrodeInfo.mat"), "rb"
        )
        self.file_spock_stl = open(
            os.path.join(TEST_DIR + "/files", "Spock_HPC.stl"), "rb"
        )

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT)

    def test_upload_bad_file_extension(self):
        spock = BuffaloSubject.objects.get(nickname="Spock")
        stl_add_url = reverse("admin:buffalo_stlfile_add") + f"?subject={spock.id}"
        resp = self.client.post(
            stl_add_url,
            {"stl_file": self.file_spock_mat, "subject": spock.id},
            format="multipart",
        )
        self.assertContains(resp, "File extension “mat” is not allowed")

    def test_upload_well(self):
        spock = BuffaloSubject.objects.get(nickname="Spock")
        stl_add_url = reverse("admin:buffalo_stlfile_add") + f"?subject={spock.id}"
        resp = self.client.post(
            stl_add_url,
            {
                "name": "hpc",
                "stl_file": self.file_spock_stl,
                "subject": spock.id,
                "sync_electrodelogs": False
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(resp, "File uploaded successful")
        stl_files = STLFile.objects.filter(subject=spock.id)
        self.assertEquals(1, len(stl_files))
