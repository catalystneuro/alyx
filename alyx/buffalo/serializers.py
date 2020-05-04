from rest_framework import serializers

from .models import BehavioralTask
from misc.models import LabMember
from actions.models import Session
from data.models import DatasetType
from experiments.models import Channel


class BehavioralTaskSerializer(serializers.HyperlinkedModelSerializer):
    """ dataset_type = serializers.SlugRelatedField(
        read_only=False, slug_field="name", queryset=DatasetType.objects.all(),
    )
 """
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
            #"dataset_type",
            "date_time",
            "lab_member",
            "weight",
            "menstration",
            "general_comments",
            "session",
            "task_sequence",
        )
