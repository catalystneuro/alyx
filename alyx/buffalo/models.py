from django.db import models
from django.utils import timezone
from django.db.models import Count
from django.core.validators import MinValueValidator, FileExtensionValidator
from django.db import transaction, IntegrityError
from django.conf import settings

from alyx.base import BaseModel
from data.models import DatasetType, Dataset
from actions.models import Session, Weighing, BaseAction
from subjects.models import Subject
import trimesh
from trimesh import proximity


FOOD_UNITS = [
    ("ml", "ML"),
    ("bucket", "Bucket"),
    ("gr", "gr"),
]

NUMBER_OF_CELLS = [
    ("1", "nothing"),
    ("2", "maybe 1 cell"),
    ("3", "1 good cell"),
    ("4", "2+ good cells"),
]

RIPPLES = [
    ("yes", "Yes"),
    ("no", "No"),
    ("maybe", "Maybe"),
]

ALIVE = [
    ("yes", "Yes"),
    ("no", "No"),
    ("maybe", "Maybe"),
]

CHAMBER_CLEANING = [
    ("yes", "Yes"),
    ("no", "No"),
    ("n/a", "N/A"),
]


class Location(BaseModel):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Reward(BaseModel):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TaskCategory(BaseModel):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Platform(BaseModel):
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class NeuralPhenomena(BaseModel):
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class BuffaloSubject(Subject):
    unique_id = models.CharField(
        max_length=255, blank=True, default="", help_text="Monkey Identifier"
    )
    code = models.CharField(
        max_length=2, blank=True, default="", help_text="Two letter code"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class BuffaloElectrodeSubject(BuffaloSubject):
    class Meta:
        proxy = True


class BuffaloElectrodeLogSubject(BuffaloSubject):
    class Meta:
        proxy = True


class BuffaloDeviceSubject(BuffaloSubject):
    class Meta:
        proxy = True


class Task(BaseModel):
    name = models.CharField(max_length=255, blank=True, help_text="Task name")
    description = models.TextField(blank=True)
    platform = models.ForeignKey(
        Platform, null=True, blank=True, on_delete=models.SET_NULL, default=None
    )
    category = models.ForeignKey(
        TaskCategory, null=True, blank=True, on_delete=models.SET_NULL
    )
    location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL
    )
    reward = models.ForeignKey(Reward, null=True, blank=True, on_delete=models.SET_NULL)

    training = models.BooleanField(default=False)
    original_task = models.CharField(
        blank=True, null=True, max_length=255, help_text="Task version"
    )
    first_version = models.BooleanField(default=True)
    version = models.CharField(
        blank=True, null=True, max_length=255, help_text="Task version", default="1"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "TaskType"


class SessionTask(BaseModel):
    task = models.ForeignKey(Task, null=True, blank=True, on_delete=models.SET_NULL)
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    general_comments = models.TextField(blank=True)
    session = models.ForeignKey(
        Session, null=True, blank=True, on_delete=models.SET_NULL
    )
    dataset_type = models.ManyToManyField(DatasetType, blank=True)
    task_sequence = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Indicates the relative position of a task within the session it belongs to",
    )
    needs_review = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Task"
        unique_together = (
            "session",
            "task_sequence",
        )


class FoodType(BaseModel):
    unit = models.CharField(max_length=255, choices=FOOD_UNITS, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        str_food_log = f"{self.name} - ({self.unit})"
        return str_food_log


class FoodLog(BaseModel):
    subject = models.ForeignKey(
        BuffaloSubject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which this action was performed",
    )
    food = models.ForeignKey(FoodType, null=True, blank=True, on_delete=models.PROTECT)
    amount = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(limit_value=0)]
    )
    session = models.ForeignKey(
        Session, null=True, blank=True, on_delete=models.SET_NULL
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.food.name

    def get_food_detail(self):
        food_detail = f"{self} {self.amount} ({self.food.unit})"
        return food_detail


class WeighingLog(Weighing):
    session = models.ForeignKey(
        Session, null=True, blank=True, on_delete=models.SET_NULL
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        str_weight = f"{self.weight} kg"
        return str_weight


class MenstruationLog(BaseModel):
    subject = models.ForeignKey(
        BuffaloSubject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which this action was performed",
    )
    session = models.ForeignKey(
        Session, null=True, blank=True, on_delete=models.SET_NULL
    )
    menstruation = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class BuffaloDataset(Dataset):
    file_name = models.CharField(
        blank=True, null=True, max_length=255, help_text="file name"
    )
    session_task = models.ForeignKey(
        SessionTask, null=True, blank=True, on_delete=models.SET_NULL
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class BuffaloSession(Session):
    needs_review = models.BooleanField(default=False)
    pump_setting = models.FloatField(null=True, blank=True)
    chamber_cleaning = models.CharField(
        max_length=10, choices=CHAMBER_CLEANING, null=True, blank=True
    )
    unknown_user = models.CharField(
        blank=True, null=True, max_length=255, help_text="Unknown user initials"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Session"

    def save(self, block_table=True, *args, **kwargs):
        if not self.pk and block_table:
            with transaction.atomic():
                subject_sessions = BuffaloSession.objects.filter(
                    subject=self.subject,
                    start_time=self.start_time
                ).exists()
                BuffaloSession.objects.select_for_update().all()
                if subject_sessions:
                    raise IntegrityError("This Session already exists.")
                return super(BuffaloSession, self).save(*args, **kwargs)
        return super(BuffaloSession, self).save(*args, **kwargs)


class Device(BaseModel):
    subject = models.ForeignKey(
        BuffaloSubject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which the device is",
    )
    implantation_date = models.DateTimeField(null=True, blank=True, default=timezone.now)
    explantation_date = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = "deleted"
        if self.subject:
            name = self.subject.nickname
        return f"{name} - {self.name}"


class BuffaloElectrodeDevice(Device):
    class Meta:
        proxy = True


class Electrode(BaseAction):
    subject = models.ForeignKey(
        BuffaloSubject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which the electrode is",
    )
    device = models.ForeignKey(
        Device,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="device",
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    millimeters = models.FloatField(null=True, blank=True)
    turns_per_mm = models.FloatField(null=True, blank=True, default=8)
    channel_number = models.CharField(max_length=255, default="", blank=True)
    notes = models.CharField(max_length=255, default="", blank=True)
    procedures = models.ManyToManyField(
        "actions.ProcedureType", blank=True, help_text="The procedure(s) performed"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def current_location(self):
        """queries related channel recordings"""
        starting_point = self.starting_point.latest("updated")
        location = {"x": starting_point.x, "y": starting_point.y, "z": starting_point.z}
        return location

    def create_new_starting_point_from_mat(
        self, electrode_info, subject, starting_point_set
    ):
        starting_point = StartingPoint()
        starting_point.x = electrode_info["start_point"][0]
        starting_point.y = electrode_info["start_point"][1]
        starting_point.z = electrode_info["start_point"][2]
        starting_point.x_norm = electrode_info["norms"][0]
        starting_point.y_norm = electrode_info["norms"][1]
        starting_point.z_norm = electrode_info["norms"][2]
        starting_point.electrode = self
        starting_point.subject = subject
        starting_point.starting_point_set = starting_point_set
        starting_point.save()

    def is_in_location(self, stl):
        return self.current_location in stl

    def __str__(self):
        device_name = "device-deleted"
        subject_name = "subject-deleted"
        if self.device:
            device = self.device
            device_name = device.name
            if device.subject:
                subject = device.subject
                subject_name = subject.nickname
        return f"{subject_name} - {device_name} - {self.channel_number}"


class ElectrodeLog(BaseAction):
    electrode = models.ForeignKey(
        Electrode, on_delete=models.SET_NULL, null=True, blank=True,
    )
    turn = models.FloatField(null=True, blank=True)
    impedance = models.FloatField(null=True, blank=True)
    notes = models.CharField(max_length=255, default="", blank=True)
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    procedures = models.ManyToManyField(
        "actions.ProcedureType", blank=True, help_text="The procedure(s) performed"
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_current_location(self):
        electrode = self.electrode
        location = {}
        if electrode and len(electrode.starting_point.all()) > 0:
            starting_point = electrode.starting_point.latest("updated")
            if self.turn is not None:
                distance = self.turn / self.electrode.turns_per_mm
                location_list = starting_point.get_norms()
                initial_position = starting_point.get_start_position()
                for i in range(len(location_list)):
                    location_list[i] *= distance
                    location_list[i] += initial_position[i]
                location = {
                    "x": location_list[0],
                    "y": location_list[1],
                    "z": location_list[2],
                }
        return location

    def is_in_stl(self, stl_file_name):
        electrode = self.electrode
        if electrode and len(electrode.starting_point.all()) > 0:
            if self.turn is not None:
                curr_location = self.get_current_location()
                location_list = [
                    curr_location["x"],
                    curr_location["y"],
                    curr_location["z"],
                ]
                mesh = trimesh.load(settings.UPLOADED_PATH + stl_file_name)
                dist = proximity.signed_distance(mesh, [location_list])
                if dist[0] > 0:
                    return True, dist[0]
                else:
                    return False, dist[0]
        return False, None

    @property
    def current_location(self):
        location = self.get_current_location()
        return str(location)

    @property
    def is_in_stls(self):
        stls = {}
        elstls = ElectrodeLogSTL.objects.prefetch_related('stl').filter(
            electrodelog=self
        )
        for elstl in elstls:
            stl = elstl.stl
            name = str(stl)
            if stl.name:
                name = stl.name
            stls[name] = f"{str(elstl.is_in)} ({elstl.distance})"
        return stls

    def save(self, sync=True, *args, **kwargs):
        super(ElectrodeLog, self).save(*args, **kwargs)
        if sync:
            ell = ElectrodeLog.objects.prefetch_related('electrode__device__subject').get(
                pk=self.id
            )
            existing = ell.electrodelogstl.prefetch_related("stl").all().values("id")
            subject = ell.electrode.device.subject
            stls = STLFile.objects.filter(subject=subject).exclude(id__in=existing)
            for stl in stls:
                elstl = ElectrodeLogSTL(
                    stl=stl,
                    electrodelog=self
                )
                elstl.is_in, elstl.distance = self.is_in_stl(stl.stl_file.name)
                elstl.save()

    def sync_stl(self, stl):
        elstl = ElectrodeLogSTL(
            stl=stl,
            electrodelog=self
        )
        is_in, distance = self.is_in_stl(stl.stl_file.name)
        if is_in or distance is not None:
            elstl.is_in = is_in
            elstl.distance = distance
            elstl.save()


class StartingPointSet(BaseModel):
    name = models.CharField(max_length=255, default="", blank=True)
    subject = models.ForeignKey(BuffaloSubject, null=True, on_delete=models.SET_NULL,)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class StartingPoint(BaseAction):
    electrode = models.ForeignKey(
        Electrode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="starting_point",
    )
    x = models.FloatField(null=True)
    y = models.FloatField(null=True)
    z = models.FloatField(null=True)
    x_norm = models.FloatField(null=True)
    y_norm = models.FloatField(null=True)
    z_norm = models.FloatField(null=True)
    depth = models.FloatField(null=True, blank=True)
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    notes = models.CharField(max_length=255, default="", blank=True)
    procedures = models.ManyToManyField(
        "actions.ProcedureType", blank=True, help_text="The procedure(s) performed"
    )
    starting_point_set = models.ForeignKey(
        StartingPointSet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="starting_point",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_start_position(self):
        return [self.x, self.y, self.z]

    def get_norms(self):
        return [self.x_norm, self.y_norm, self.z_norm]


def stl_directory_path(instance, filename):
    return "stl/subject_{0}/{1}".format(instance.subject.id, filename)


class STLFile(Dataset):
    stl_file = models.FileField(
        upload_to=stl_directory_path, validators=[FileExtensionValidator(["stl"])]
    )
    subject = models.ForeignKey(
        BuffaloSubject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which the electrode is",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        date = self.created_datetime.strftime("%d/%m/%Y at %H:%M")
        name = "deleted"
        if self.subject:
            name = self.subject.nickname
        name_stl = ""
        if self.name:
            name_stl = self.name
        else:
            name_stl = str(self.pk)[:8]
        return "<Dataset %s - %s created on %s>" % (name_stl, name, date)

    def sync_electrodelogs(self):
        subject = self.subject
        stls = STLFile.objects.filter(subject=subject)
        electrode_logs = ElectrodeLog.objects.filter(
            electrode__device__subject=subject
        ).annotate(
            num_stls=Count('electrodelogstl')
        ).filter(num_stls__lt=len(stls))

        for electrode_log in electrode_logs:
            electrode_log.sync_stl(self)


class ElectrodeLogSTL(BaseModel):
    electrodelog = models.ForeignKey(
        ElectrodeLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="electrodelogstl",
    )
    stl = models.ForeignKey(
        STLFile, on_delete=models.SET_NULL, null=True, blank=True,
    )
    is_in = models.BooleanField(default=False)
    distance = models.FloatField(null=True, blank=True, default=None)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class BuffaloAsyncTask(BaseModel):
    PENDING = "PEN"
    COMPLETED = "COM"
    ERROR = "ERR"
    STATUS = (
        (PENDING, "PENDING"),
        (COMPLETED, "COMPLETED"),
        (ERROR, "ERROR"),
    )
    description = models.CharField(max_length=255, default="", blank=True)
    status = models.CharField(max_length=3, default=PENDING, choices=STATUS)
    message = models.CharField(max_length=255, default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ChannelRecording(BaseModel):
    electrode = models.ForeignKey(
        Electrode, null=True, blank=True, on_delete=models.SET_NULL
    )
    ripples = models.CharField(max_length=180, choices=RIPPLES, default="", blank=True)
    notes = models.CharField(max_length=255, default="", blank=True)
    alive = models.CharField(max_length=180, choices=ALIVE, default="", blank=True)
    number_of_cells = models.CharField(
        max_length=255, choices=NUMBER_OF_CELLS, default="", blank=True
    )
    session = models.ForeignKey(
        Session, null=True, blank=True, on_delete=models.SET_NULL
    )
    neural_phenomena = models.ManyToManyField(NeuralPhenomena, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            "electrode",
            "session",
        )


class ProcessedRecording(Dataset):
    """sam_unitstracking sheet 2 two can be created by querying this model"""

    source = models.CharField(
        max_length=1000, blank=True, help_text="Path to source file"
    )
    electrical_voltage_file = models.CharField(
        max_length=1000, blank=True, help_text="Path to result file"
    )
    channel_recording = models.ForeignKey(
        ChannelRecording, on_delete=models.SET_NULL, null=True, blank=True
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    lfp_band_1 = models.FloatField(null=True, blank=True)
    lfp_band_2 = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
