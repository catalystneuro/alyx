from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator

from alyx.base import BaseModel
from alyx.data import DatasetType
from misc.models import HousingSubject, LabMember

MAZE_TYPES = [
    ("Y-maze", "Y-maze"),
    ("calibration", "Calibration"),
]

REWARD_TYPES = [
    ("juice", "Juice"),
]


class BehavioralTask(BaseModel):
    maze_type = models.CharField(max_length=1, choices=MAZE_TYPES, blank=True)
    reward_type = models.CharField(
        max_length=1, choices=REWARD_TYPES, default=None, blank=True
    )
    # quality_metrics
    version = models.CharField(
        blank=True, null=True, max_length=64, help_text="generating software revision"
    )
    dataset_type = models.ManyToManyField(DatasetType, blank=True)


class FoodConsumption(BaseModel):
    amount = models.FloatField(null=True, validators=[MinValueValidator(limit_value=0)])
    housing_subject = models.ForeignKey(
        HousingSubject, on_delete=models.SET_NULL, null=True, blank=True
    )
    lab_member = models.ForeignKey(
        LabMember, on_delete=models.SET_NULL, null=True, blank=True
    )
    date_time = models.DateTimeField(null=True, blank=True, default=timezone.now)
