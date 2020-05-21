from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from django.conf import settings

from alyx.base import BaseModel
from data.models import DatasetType, Dataset
from misc.models import HousingSubject, LabMember
from actions.models import Session, Weighing
from subjects.models import Subject


TASK_CATEGORY = [
    ("task1", "Task 1"),
]

MAZE_TYPES = [
    ("Y-maze", "Y-maze"),
    ("calibration", "Calibration"),
]

REWARD_TYPES = [
    ("juice", "Juice"),
]

UNITS = [
    ("none", "0"),
    ("few", "1"),
    ("lots", "2"),
]

NUMBER_OF_CELLS = [
    ('1', "nothing"),
    ('2', "maybe 1 cell"),
    ('3', "1 good cell"),
    ('4', "2+ good cells"),
]


class Task(BaseModel):
    name = models.CharField(max_length=255, blank=True, help_text="Task name")
    description = models.TextField(blank=True)
    category = models.CharField(
        max_length=255, choices=TASK_CATEGORY, default=None, blank=True
    )
    reward_type = models.CharField(
        max_length=255, choices=REWARD_TYPES, default=None, blank=True
    )
    maze_type = models.CharField(max_length=125, choices=MAZE_TYPES, blank=True)
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
    dataset_type = models.ManyToManyField(DatasetType, blank=True)
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    general_comments = models.TextField(blank=True)
    session = models.ForeignKey(
        Session, null=True, blank=True, on_delete=models.SET_NULL
    )
    task_sequence = models.PositiveSmallIntegerField(
        blank=True,
        help_text="Indicates the relative position of a task within the session it belongs to",
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    

class FoodConsumption(BaseModel):
    amount = models.FloatField(null=True, validators=[MinValueValidator(limit_value=0)])
    food = models.FloatField(
        validators=[
            MinValueValidator(limit_value=50),
            MaxValueValidator(limit_value=1500),
        ],
        default=None,
        help_text="Food in Ml",
    )
    note = models.TextField(blank=True, help_text="If supplemented make note")
    housing_subject = models.ForeignKey(
        HousingSubject, on_delete=models.SET_NULL, null=True, blank=True
    )
    lab_member = models.ForeignKey(
        LabMember, on_delete=models.SET_NULL, null=True, blank=True
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class SubjectFood(BaseModel):
    subject = models.ForeignKey(
        Subject,
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


class DailyObservation(models.Model):
    subject = models.ForeignKey(
        Subject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which this action was performed",
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    run = models.BooleanField(default=False)
    food = models.ForeignKey(
        FoodConsumption, on_delete=models.SET_NULL, null=True, blank=True
    )
    general_comments = models.TextField(blank=True)
    lab_member = models.ForeignKey(
        LabMember, on_delete=models.SET_NULL, null=True, blank=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

class Electrode(models.Model):
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    turn = models.FloatField()
    millimeters = models.FloatField(null=True, blank=True)
    impedance = models.FloatField(null=True, blank=True)
    units = models.CharField(max_length=255, choices=UNITS, default="", blank=True)
    subject = models.ForeignKey(
        Subject,
        null=True,
        on_delete=models.SET_NULL,
        help_text="The subject on which the electrode is",
    )
    notes = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def current_location(self):
        """queries related channel recordings"""
        starting_point = self.starting_point.latest("updated")
        location = {"x": starting_point.x, "y": starting_point.y, "z": starting_point.y}
        return location

    def is_in_location(self, stl):
        return self.current_location in stl

    def __str__(self):
        return self.subject.nickname


class StartingPoint(models.Model):
    lab_member = models.ForeignKey(
        LabMember, on_delete=models.SET_NULL, null=True, blank=True
    )
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
    orientation = models.CharField(max_length=128, blank=True)
    notes = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class STLFile(Dataset):
    stl_file = models.CharField(
        max_length=1000, blank=True, help_text="Path to STL file"
    )
    subject = models.ForeignKey(
        Subject,
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
    session_task = models.ForeignKey(
        SessionTask, null=True, blank=True, on_delete=models.SET_NULL
    )
    stl_file = models.ForeignKey(
        STLFile, null=True, blank=True, on_delete=models.SET_NULL
    )
    alive = models.BooleanField(default=False)
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
