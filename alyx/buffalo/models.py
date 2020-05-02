from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from alyx.base import BaseModel
from data.models import DatasetType
from misc.models import HousingSubject, LabMember
from actions.models import Session

MAZE_TYPES = [
    ("Y-maze", "Y-maze"),
    ("calibration", "Calibration"),
]

REWARD_TYPES = [
    ("juice", "Juice"),
]


class BehavioralTask(BaseModel):
    # maze_type = models.CharField(max_length=1, choices=MAZE_TYPES, blank=True)
    reward_type = models.CharField(
        max_length=255, choices=REWARD_TYPES, default=None, blank=True
    )
    # quality_metrics
    version = models.CharField(
        blank=True, null=True, max_length=64, help_text="generating software revision"
    )
    dataset_type = models.ManyToManyField(DatasetType, blank=True)
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
    lab_member = models.ForeignKey(
        LabMember, on_delete=models.SET_NULL, null=True, blank=True
    )
    weight = models.FloatField(
        validators=[
            MinValueValidator(limit_value=0),
            MaxValueValidator(limit_value=35),
        ],
        help_text="Weight in Kg",
    )
    food = models.FloatField(
        validators=[
            MinValueValidator(limit_value=50),
            MaxValueValidator(limit_value=1500),
        ],
        help_text="Food in Ml",
    )
    food_note = models.TextField(blank=True, help_text="If supplemented make note")
    menstration = models.BooleanField(default=False)
    general_comments = models.TextField(blank=True)
    session = models.ForeignKey(
        Session, null=True, blank=True, on_delete=models.SET_NULL
    )
    task_sequence = models.PositiveSmallIntegerField(
        blank=True,
        help_text="Indicates the relative position of a task within the session it belongs to",
    )


class FoodConsumption(BaseModel):
    amount = models.FloatField(null=True, validators=[MinValueValidator(limit_value=0)])
    housing_subject = models.ForeignKey(
        HousingSubject, on_delete=models.SET_NULL, null=True, blank=True
    )
    lab_member = models.ForeignKey(
        LabMember, on_delete=models.SET_NULL, null=True, blank=True
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
