from django.db import models
from django.utils import timezone


from alyx.base import BaseModel
from data.models import DatasetType, Dataset
from misc.models import LabMember, Food
from actions.models import Session, Weighing, BaseAction, ProcedureType 
from subjects.models import Subject


UNITS = [
    ("none", "0"),
    ("few", "1"),
    ("lots", "2"),
]

NUMBER_OF_CELLS = [
    ("1", "nothing"),
    ("2", "maybe 1 cell"),
    ("3", "1 good cell"),
    ("4", "2+ good cells"),
]

RIPLES = [
    ("yes", "Yes"),
    ("no", "No"),
    ("maybe", "Maybe"),
]

ALIVE = [
    ("yes", "Yes"),
    ("no", "No"),
    ("maybe", "Maybe"),
]


class Location(BaseModel):
    def __str__(self):
        return self.name


class Reward(BaseModel):
    def __str__(self):
        return self.name


class TaskCategory(BaseModel):
    def __str__(self):
        return self.name


class Platform(BaseModel):
    def __str__(self):
        return self.name


class BuffaloSubject(Subject):
    unique_id = models.CharField(
        max_length=255, blank=True, default="", help_text="Monkey Identifier"
    )
    code = models.CharField(
        max_length=2, blank=True, default="", help_text="Two letter code"
    )
    #created = models.DateTimeField(auto_now_add=True)
    #updated = models.DateTimeField(auto_now=True)


class BuffaloElectrodeSubject(BuffaloSubject):

    class Meta:
        proxy = True

class BuffaloElectrodeLogSubject(BuffaloSubject):

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
    dataset_type = models.ManyToManyField(DatasetType, blank=True)
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
        if self.version is None:
            return self.name
        return f"{self.name} (version: {self.version})"


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
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class SubjectFood(BaseModel):
    subject = models.ForeignKey(
        BuffaloSubject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which this action was performed",
    )
    amount = models.FloatField(null=True, blank=True)
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject.nickname


class Electrode(models.Model):
    subject = models.ForeignKey(
        BuffaloSubject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which the electrode is",
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    millimeters = models.FloatField(null=True, blank=True)
    turns_per_mm = models.FloatField(null=True, blank=True, default=8)
    channel_number = models.CharField(max_length=255, default="", blank=True)
    notes = models.CharField(max_length=255, default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def current_location(self):
        """queries related channel recordings"""
        starting_point = self.starting_point.latest("updated")
        location = {"x": starting_point.x, "y": starting_point.y, "z": starting_point.z}
        return location
    
    def create_new_starting_point_from_mat(self, electrode_info):
        starting_point = StartingPoint()
        starting_point.x = electrode_info['start_point'][0]
        starting_point.y = electrode_info['start_point'][1]
        starting_point.z = electrode_info['start_point'][2]
        starting_point.x_norm = electrode_info['norms'][0]
        starting_point.y_norm = electrode_info['norms'][1]
        starting_point.z_norm = electrode_info['norms'][2]
        starting_point.electrode = self
        starting_point.save()

    def is_in_location(self, stl):
        return self.current_location in stl

    def __str__(self):
        return f"{self.subject.nickname} - {self.channel_number}"


class ElectrodeLog(BaseAction):
    electrode = models.ForeignKey(
        Electrode, 
        on_delete=models.SET_NULL, 
        null=True,
        blank=True,
    )
    turn = models.FloatField(null=True, blank=True)
    impedance = models.FloatField(null=True, blank=True)
    notes = models.CharField(max_length=255, default="", blank=True)
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    procedures = models.ManyToManyField('actions.ProcedureType', blank=True,
                                        help_text="The procedure(s) performed")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def current_location(self):
        """queries related channel recordings"""
        starting_point = self.electrode.starting_point.latest("updated")
        location = {"x": starting_point.x, "y": starting_point.y, "z": starting_point.z}
        if self.turn:
            distance = (self.turn / self.electrode.turns_per_mm)
            location_list = starting_point.get_norms()
            initial_position = starting_point.get_start_position()
            for i in range(len(location_list)):
                location_list[i] *= distance
                location_list[i] += initial_position[i]
            location = {"x": location_list[0], "y": location_list[1], "z": location_list[2]}
        return str(location)


class StartingPoint(models.Model):
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
    lab_member = models.ForeignKey(
        LabMember, on_delete=models.SET_NULL, null=True, blank=True
    )
    depth = models.FloatField(null=True, blank=True)
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    notes = models.CharField(max_length=255, default="", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_start_position(self):
        return [self.x, self.y, self.z]

    def get_norms(self):
        return [self.x_norm, self.y_norm, self.z_norm]

class STLFile(Dataset):
    stl_file = models.CharField(
        max_length=1000, blank=True, help_text="Path to STL file"
    )
    subject = models.ForeignKey(
        BuffaloSubject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which the electrode is",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ChannelRecording(models.Model):
    electrode = models.ForeignKey(
        Electrode, null=True, blank=True, on_delete=models.SET_NULL
    )
    riples = models.CharField(max_length=180, choices=RIPLES, default="", blank=True)
    notes = models.CharField(max_length=255, default="", blank=True)
    alive = models.CharField(max_length=180, choices=ALIVE, default="", blank=True)
    number_of_cells = models.CharField(
        max_length=255, choices=NUMBER_OF_CELLS, default="", blank=True
    )
    session = models.ForeignKey(
        Session, null=True, blank=True, on_delete=models.SET_NULL
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


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
