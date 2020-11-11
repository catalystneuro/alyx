import os
import tempfile
import shutil
from django.utils import timezone
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from buffalo.tasks import (
    sync_electrodelogs_device,
    sync_electrodelogs_stl
)

from buffalo.models import (
    BuffaloSubject,
    STLFile,
    Device,
    Electrode,
    ElectrodeLog,
    ElectrodeLogSTL,
    StartingPoint
)


TEST_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_ROOT = tempfile.mkdtemp()
UPLOADED_PATH = MEDIA_ROOT + "/"


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class STLUploadTests(TestCase):
    def setUp(self):
        User = get_user_model()
        my_admin = User.objects.create_superuser("admin", "admin@test.com", "123456")
        self.client = Client()
        self.client.force_login(my_admin)

        spock, _ = BuffaloSubject.objects.get_or_create(nickname="Spock")

        dev, _ = Device.objects.get_or_create(
            subject=spock,
            name="posterior",
            implantation_date=str(timezone.now()),
            explantation_date=str(timezone.now())
        )
        el_77, _ = Electrode.objects.get_or_create(
            channel_number="77",
            device=dev,
            subject=spock,
            turns_per_mm=float(8)
        )
        StartingPoint.objects.get_or_create(
            electrode=el_77,
            x=-19.1135333196784,
            y=42.9596923266085,
            z=1.72192261925612,
            x_norm=0.0765529674660019,
            y_norm=-0.985815829571632,
            z_norm=-0.14935454272781,
            subject=spock
        )
        ElectrodeLog.objects.get_or_create(
            electrode=el_77,
            subject=spock,
            turn=float(255)
        )

        el_78, _ = Electrode.objects.get_or_create(
            channel_number="78",
            device=dev,
            subject=spock,
            turns_per_mm=float(8)
        )
        StartingPoint.objects.get_or_create(
            electrode=el_78,
            x=-20.5469501630928,
            y=41.7317947874531,
            z=1.55765361697747,
            x_norm=0.0765529674660019,
            y_norm=-0.985815829571632,
            z_norm=-0.14935454272781,
            subject=spock
        )

        ElectrodeLog.objects.get_or_create(
            electrode=el_78,
            subject=spock,
            turn=255
        )

        # Open file
        self.file_spock_stl = open(
            os.path.join(TEST_DIR + "/files", "Spock_HPC.stl"), "rb"
        )

    def tearDown(self):
        shutil.rmtree(MEDIA_ROOT)

    @override_settings(UPLOADED_PATH=UPLOADED_PATH)
    def test_sync_electrodelogs_device(self):
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

        dev = Device.objects.get(
            subject=spock,
            name="posterior"
        )

        sync_electrodelogs_device(dev.id)

        ellstls = ElectrodeLogSTL.objects.all()
        self.assertEquals(2, len(ellstls))

        elstl_77 = ElectrodeLogSTL.objects.get(
            electrodelog__electrode__channel_number="77"
        )
        self.assertEquals(True, elstl_77.is_in)

        elstl_78 = ElectrodeLogSTL.objects.get(
            electrodelog__electrode__channel_number="78"
        )
        self.assertEquals(False, elstl_78.is_in)

    @override_settings(UPLOADED_PATH=UPLOADED_PATH)
    def test_sync_electrodelogs_stl(self):

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

        sync_electrodelogs_stl(stl_files[0].id)

        ellstls = ElectrodeLogSTL.objects.all()
        self.assertEquals(2, len(ellstls))

        elstl_77 = ElectrodeLogSTL.objects.get(
            electrodelog__electrode__channel_number="77"
        )
        self.assertEquals(True, elstl_77.is_in)

        elstl_78 = ElectrodeLogSTL.objects.get(
            electrodelog__electrode__channel_number="78"
        )
        self.assertEquals(False, elstl_78.is_in)
