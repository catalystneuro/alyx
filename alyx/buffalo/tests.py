from django.test.testcases import TestCase

from django.conf import settings
from buffalo.models import BuffaloSubject
from misc.models import Lab, LabMember

class SubjectTestCase(TestCase):
    def setUp(self):
        #import pdb; pdb.set_trace()
        self.lab = Lab.objects.create(name='testlab')
        self.user = LabMember.objects.create(username='test1')
        self.subject = BuffaloSubject.objects.create(
            nickname='test', birth_date=('2018-01-01'), lab=self.lab,
            responsible_user=self.user)

        
    
    def test_subject_exists(self):
        self.assertTrue(BuffaloSubject.objects.filter(nickname='test').exists())

    def tearDown(self):
        self.user.delete()