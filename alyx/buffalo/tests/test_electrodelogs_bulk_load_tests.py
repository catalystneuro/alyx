import os
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files import File
from django.contrib.auth import get_user_model

from buffalo.models import BuffaloSubject, Electrode, ElectrodeLog

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

class BulkLoadTests(TestCase):

    def setUp(self):
        User = get_user_model()
        my_admin = User.objects.create_superuser('admin', 'admin@test.com', '123456')
        self.client = Client()
        self.client.force_login(my_admin)

        sam = BuffaloSubject.objects.get_or_create(nickname="Sam")
        for i in range(1, 97):
            Electrode.objects.get_or_create(subject=sam, channel_number=i)

        # Open file
        self.file_sam_xlsm = open(os.path.join(TEST_DIR + '/files', 'SamAnteriorElectrodeTracking.xlsm'), 'rb')
        self.file_sam_xlsm_wrong = open(os.path.join(TEST_DIR + '/files', 'SamAnteriorElectrodeTrackingWrong.xlsm'), 'rb')
    
    def test_upload_bad_structure(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        bulk_load_url = \
            reverse("electrodelog-bulk-load", kwargs={'subject_id': sam.id})
        resp = self.client.post(
            bulk_load_url, 
            {
                'file': self.file_spock_stl_wrong,
                'subject': sam.id,
            }
            , format='multipart'
        )
        self.assertContains(resp, "The structure of this file is wrong.")
    
    def test_upload_bad_file_extension(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        bulk_load_url = \
            reverse("electrodelog-bulk-load", kwargs={'subject_id': sam.id})
        resp = self.client.post(
            bulk_load_url, 
            {
                'file': self.file_spock_stl,
                'subject': sam.id,
            }
            , format='multipart'
        )
        self.assertContains(resp, "File extension should be “xlsm”")

    def test_upload_well(self):
        sam = BuffaloSubject.objects.get(nickname="Sam")
        bulk_load_url = \
            reverse("electrodelog-bulk-load", kwargs={'subject_id': sam.id})
        resp = self.client.post(
            bulk_load_url, 
            {
                'file': self.file_sam_xlsm,
                'subject': sam.id,
            },
            follow=True,
            format='multipart'
        )
        self.assertContains(resp, "File loaded successful")
        electrode_47 = Electrode.objects.filter(subject=sam, channel_number=47)
        electrodelogs_47 = ElectrodeLog.objects.filter(electrode=electrode_47)
        self.assertEquals(20, len(electrodelogs_47))
        electrode_74 = Electrode.objects.filter(subject=sam, channel_number=74)
        electrodelogs_74 = ElectrodeLog.objects.filter(electrode=electrode_74)
        self.assertEquals(17, len(electrodelogs_74))