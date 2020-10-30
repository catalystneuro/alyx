import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from buffalo.models import (
    BuffaloSubject, Electrode, Device, ChannelRecording, BuffaloSession
)

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class ChannelRecordingsBulkLoadTests(TestCase):
    def setUp(self):
        User = get_user_model()
        my_admin = User.objects.create_superuser("admin", "admin@test.com", "123456")
        self.client = Client()
        self.client.force_login(my_admin)

        sam = BuffaloSubject.objects.get_or_create(nickname="Sam")[0]
        dsamp = Device.objects.get_or_create(name="posterior-sam", subject=sam)[0]
        dsama = Device.objects.get_or_create(name="anterior-sam", subject=sam)[0]
        # 331 sesiones
        for i in range(1, 125):
            Electrode.objects.get_or_create(subject=sam, device=dsamp, channel_number=i)
        for i in range(1, 97):
            Electrode.objects.get_or_create(subject=sam, device=dsama, channel_number=i)

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
        dsamp = Device.objects.get(name="posterior-sam", subject=sam)
        bulk_load_url = reverse(
            "channelrecord-bulk-load", kwargs={"subject_id": sam.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_sam_xlsx_wrong,
                "device": dsamp,
                "subject": sam.id,
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(resp, "Error loading the file")

    def test_upload_bad_file_extension(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        dsamp = Device.objects.get(name="posterior-sam", subject=sam)
        bulk_load_url = reverse(
            "channelrecord-bulk-load", kwargs={"subject_id": sam.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_spock_mat,
                "device": dsamp.id,
                "subject": sam.id,
            },
            format="multipart",
        )
        self.assertContains(
            resp, "File extension “mat” is not allowed. Allowed extensions are: xlsx."
        )

    def test_upload_well(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        dsamp = Device.objects.get(name="posterior-sam", subject=sam)
        bulk_load_url = reverse(
            "channelrecord-bulk-load", kwargs={"subject_id": sam.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_sam_xlsx,
                "device": dsamp.id,
                "subject": sam.id,
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(resp, "File loaded successful")
        session_name = "2018-05-03 00:00:00_Sam"
        session_180503 = BuffaloSession.objects.get(
            subject=sam, name=session_name
        )
        ch_rec_180503 = ChannelRecording.objects.filter(
            session=session_180503
        )
        self.assertEquals(124, len(ch_rec_180503))

        session_name = "2018-06-15 00:00:00_Sam"
        session_180615 = BuffaloSession.objects.get(
            subject=sam, name=session_name
        )
        ch_rec_180615 = ChannelRecording.objects.filter(
            session=session_180615
        )
        self.assertEquals(124, len(ch_rec_180615))

    def test_upload_well_with_sufix(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        dsamp = Device.objects.get(name="posterior-sam", subject=sam)
        bulk_load_url = reverse(
            "channelrecord-bulk-load", kwargs={"subject_id": sam.id}
        )
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_sam_xlsx,
                "device": dsamp.id,
                "sufix": 'a',
                "subject": sam.id,
            },
            follow=True,
            format="multipart",
        )

        self.assertContains(resp, "File loaded successful")

        session_name = "2018-08-30 00:00:00_Sam"
        session_180830 = BuffaloSession.objects.get(
            subject=sam, name=session_name
        )
        ch_rec_180830 = ChannelRecording.objects.filter(
            session=session_180830
        )
        self.assertEquals(96, len(ch_rec_180830))

        session_name = "2018-06-15 00:00:00_Sam"
        session_180615 = BuffaloSession.objects.get(
            subject=sam, name=session_name
        )
        ch_rec_180615 = ChannelRecording.objects.filter(
            session=session_180615
        )
        self.assertEquals(65, len(ch_rec_180615))
