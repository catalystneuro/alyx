import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from buffalo.models import BuffaloSubject, Electrode

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class ChannelRecordingsBulkLoadTests(TestCase):
    def setUp(self):
        User = get_user_model()
        my_admin = User.objects.create_superuser("admin", "admin@test.com", "123456")
        self.client = Client()
        self.client.force_login(my_admin)

        sam = BuffaloSubject.objects.get_or_create(nickname="Sam")[0]
        # 331 sesiones
        for i in range(1, 125):
            Electrode.objects.get_or_create(subject=sam, channel_number=i)

        self.file_sam_xlsx = open(
            os.path.join(TEST_DIR + "/files", "Sam_UnitsTrackingCurrent.xlsx"), "rb"
        )
        self.file_sam_xlsx_wrong = open(
            os.path.join(TEST_DIR + "/files", "Sam_UnitsTrackingCurrentWrong.xlsx"),
            "rb",
        )
        self.file_spock_mat = open(
            os.path.join(TEST_DIR + "/files", "SpockTrodeInfo.mat"), "rb"
        )

    def test_upload_bad_structure(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        bulk_load_url = reverse(
            "channelrecord-bulk-load", kwargs={"subject_id": sam.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_sam_xlsx_wrong,
                "subject": sam.id,
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(resp, "Error loading the file")

    def test_upload_bad_file_extension(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        bulk_load_url = reverse(
            "channelrecord-bulk-load", kwargs={"subject_id": sam.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_spock_mat,
                "subject": sam.id,
            },
            format="multipart",
        )
        self.assertContains(
            resp, "File extension “mat” is not allowed. Allowed extensions are: xlsx."
        )

    def test_upload_well(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        bulk_load_url = reverse(
            "channelrecord-bulk-load", kwargs={"subject_id": sam.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_sam_xlsx,
                "subject": sam.id,
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(resp, "File loaded successful")
