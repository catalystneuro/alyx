import os
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from buffalo.models import BuffaloSubject, Electrode, ElectrodeLog, Device
from django.db.models import Q

TEST_DIR = os.path.dirname(os.path.abspath(__file__))


class ElectrodeLogsBulkLoadTests(TestCase):
    def setUp(self):
        User = get_user_model()
        my_admin = User.objects.create_superuser("admin", "admin@test.com", "123456")
        self.client = Client()
        self.client.force_login(my_admin)

        sam = BuffaloSubject.objects.get_or_create(nickname="Sam")[0]
        dsam = Device.objects.get_or_create(name="posterior-sam", subject=sam)[0]

        for i in range(1, 97):
            Electrode.objects.create(device=dsam, subject=sam, channel_number=i)

        # Open file
        self.file_sam_xlsm = open(
            os.path.join(TEST_DIR + "/files", "SamAnteriorElectrodeTracking.xlsm"), "rb"
        )
        self.file_spock_mat = open(
            os.path.join(TEST_DIR + "/files", "SpockTrodeInfo.mat"), "rb"
        )
        self.file_sam_xlsm_wrong = open(
            os.path.join(TEST_DIR + "/files", "SamAnteriorElectrodeTrackingWrong.xlsm"),
            "rb",
        )

    def test_upload_bad_structure(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        dsam = Device.objects.get(name="posterior-sam")
        bulk_load_url = reverse("electrodelog-bulk-load", kwargs={"subject_id": sam.id})
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_sam_xlsm_wrong,
                "device": dsam.id,
                "subject": sam.id,
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(
            resp, "Error loading the file - Sheet: Trode (66) - Row: 7 - Column: 3"
        )

    def test_upload_bad_file_extension(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        dsam = Device.objects.get(name="posterior-sam")
        bulk_load_url = reverse("electrodelog-bulk-load", kwargs={"subject_id": sam.id})
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_spock_mat,
                "device": dsam.id,
                "subject": sam.id,
            },
            format="multipart",
        )
        self.assertContains(
            resp, "File extension “mat” is not allowed. Allowed extensions are: xlsm."
        )

    def test_upload_well(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        dsam = Device.objects.get(name="posterior-sam")
        bulk_load_url = reverse("electrodelog-bulk-load", kwargs={"subject_id": sam.id})
        resp = self.client.post(
            bulk_load_url,
            {
                "file": self.file_sam_xlsm,
                "device": dsam.id,
                "subject": sam.id,
            },
            follow=True,
            format="multipart",
        )
        self.assertContains(resp, "File loaded successful")
        electrode_47 = Electrode.objects.get(device=dsam, subject=sam, channel_number=47)
        electrodelogs_47 = ElectrodeLog.objects.filter(electrode=electrode_47)
        self.assertEquals(20, len(electrodelogs_47))

        electrode_74 = Electrode.objects.get(device=dsam, subject=sam, channel_number=74)
        electrodelogs_74 = ElectrodeLog.objects.filter(electrode=electrode_74)
        self.assertEquals(17, len(electrodelogs_74))

        electrode_67 = Electrode.objects.get(device=dsam, subject=sam, channel_number=67)
        electrodelogs_67 = ElectrodeLog.objects.filter(electrode=electrode_67).filter(
            ~Q(notes="")
        )
        self.assertEquals(3, len(electrodelogs_67))

        electrode_73 = Electrode.objects.get(device=dsam, subject=sam, channel_number=73)
        electrodelogs_73 = ElectrodeLog.objects.filter(electrode=electrode_73).filter(
            ~Q(notes="")
        )
        self.assertEquals(2, len(electrodelogs_73))

        electrode_82 = Electrode.objects.get(device=dsam, subject=sam, channel_number=82)
        electrodelogs_82 = ElectrodeLog.objects.filter(electrode=electrode_82).filter(
            ~Q(impedance=None)
        )
        self.assertEquals(1, len(electrodelogs_82))

        electrode_40 = Electrode.objects.get(device=dsam, subject=sam, channel_number=40)
        electrodelogs_40 = ElectrodeLog.objects.filter(electrode=electrode_40).filter(
            ~Q(impedance=None)
        )
        self.assertEquals(0, len(electrodelogs_40))
