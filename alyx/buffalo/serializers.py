from rest_framework import serializers

from .models import BehavioralTask, UnitsTracking, TurningRecord
from misc.models import LabMember
from actions.models import Session
from data.models import DatasetType
from experiments.models import Channel


class BehavioralTaskSerializer(serializers.HyperlinkedModelSerializer):
    dataset_type = serializers.SlugRelatedField(
        read_only=False, slug_field="name", queryset="",
    )

    lab_member = serializers.SlugRelatedField(
        read_only=False, slug_field="username", queryset=LabMember.objects.all()
    )

    session = serializers.SlugRelatedField(
        many=False, read_only=False, slug_field="id", queryset=Session.objects.all()
    )

    class Meta:
        model = BehavioralTask
        fields = (
            "id",
            "name",
            "json",
            "reward_type",
            "version",
            "dataset_type",
            "date_time",
            "lab_member",
            "weight",
            "food",
            "food_note",
            "menstration",
            "general_comments",
            "session",
            "task_sequence",
        )


class UnitsTrackingSerializer(serializers.HyperlinkedModelSerializer):
    session = serializers.SlugRelatedField(
        many=False, read_only=False, slug_field="id", queryset=Session.objects.all()
    )

    class Meta:
        model = UnitsTracking
        fields = (
            "session",
            "date_time",
            "ripples",
            "ripples_channels",
            "sharp_waves",
            "sharp_waves_channels",
            "spikes_ripple",
            "spikes_ripple_channels",
            "good_behavior",
        )


class TurningRecordSerializer(serializers.HyperlinkedModelSerializer):
    task = serializers.SlugRelatedField(
        many=False,
        read_only=False,
        slug_field="id",
        queryset=BehavioralTask.objects.all(),
    )

    class Meta:
        model = TurningRecord
        fields = (
            "name",
            "task",
            "date_time",
            "turns",
            "millimeters",
            "impedance",
            "units",
            "lfp_band_1",
            "lfp_band_2",
            "notes",
        )
