import os
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files import File
from django.contrib.auth import get_user_model

from buffalo.models import BuffaloSubject, Electrode

TEST_DIR = os.path.dirname(os.path.abspath(__file__))

class BulkLoadTests(TestCase):

    def setUp(self):
        User = get_user_model()
        my_admin = User.objects.create_superuser('admin', 'admin@test.com', '123456')
        self.client = Client()
        self.client.force_login(my_admin)

        BuffaloSubject.objects.get_or_create(nickname="Horacio")
        BuffaloSubject.objects.get_or_create(nickname="Gromit")
        BuffaloSubject.objects.get_or_create(nickname="Spock")

        # Open file
        self.file_spock_mat = open(os.path.join(TEST_DIR + '/files', 'SpockTrodeInfo.mat'), 'rb')
        self.file_spock_stl = open(os.path.join(TEST_DIR + '/files', 'Spock_HPC.stl'), 'rb')
    
    def test_upload_for_another_subject(self):
        horacio = BuffaloSubject.objects.get(nickname="Horacio")
        bulk_load_url = \
            reverse("electrode-bulk-load", kwargs={'subject_id': horacio.id})
        resp = self.client.post(
            bulk_load_url, 
            {
                'file': self.file_spock_mat,
                'subject': horacio.id
            }
            , format='multipart'
        )
        self.assertContains(resp, "It cannot find an structure called: Horacio")
    
    def test_upload_for_another_subject_using_text_field(self):
        horacio = BuffaloSubject.objects.get(nickname="Horacio")
        bulk_load_url = \
            reverse("electrode-bulk-load", kwargs={'subject_id': horacio.id})
        resp = self.client.post(
            bulk_load_url, 
            {
                'file': self.file_spock_mat,
                'subject': horacio.id,
                'structure_name': 'Spock'
            },
            follow=True,
            format='multipart'
        )
        self.assertContains(resp, "File loaded successful")
    
    def test_upload_bad_file_extension(self):
        horacio = BuffaloSubject.objects.get(nickname="Horacio")
        bulk_load_url = \
            reverse("electrode-bulk-load", kwargs={'subject_id': horacio.id})
        resp = self.client.post(
            bulk_load_url, 
            {
                'file': self.file_spock_stl,
                'subject': horacio.id,
                'structure_name': 'Spock'
            }
            , format='multipart'
        )
        self.assertContains(resp, "File extension “stl” is not allowed")

    def test_upload_well(self):
        spock = BuffaloSubject.objects.get(nickname="Spock")
        bulk_load_url = \
            reverse("electrode-bulk-load", kwargs={'subject_id': spock.id})
        resp = self.client.post(
            bulk_load_url, 
            {
                'file': self.file_spock_mat,
                'subject': spock.id,
            },
            follow=True,
            format='multipart'
        )
        self.assertContains(resp, "File loaded successful")
        electrodes = Electrode.objects.filter(subject=spock.id)
        self.assertEquals(124, len(electrodes))