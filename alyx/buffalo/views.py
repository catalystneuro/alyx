from rest_framework import viewsets
from rest_framework import generics, permissions

from .serializers import (
    BehavioralTaskSerializer,
    UnitsTrackingSerializer,
    TurningRecordSerializer,
)
from .models import BehavioralTask, UnitsTracking, TurningRecord


class BehavioralTaskList(generics.ListCreateAPIView):
    serializer_class = BehavioralTaskSerializer

    def get_queryset(self):
        queryset = BehavioralTask.objects.all()
        session = self.request.query_params.get("session", None)
        if session is not None:
            queryset = queryset.filter(session=session).order_by("task_sequence")
        return queryset


class UnitsTrackingList(generics.ListCreateAPIView):
    queryset = UnitsTracking.objects.all().order_by("session")
    serializer_class = UnitsTrackingSerializer


class TurningRecordList(generics.ListCreateAPIView):
    queryset = TurningRecord.objects.all().order_by("date_time")
    serializer_class = TurningRecordSerializer
