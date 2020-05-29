from rest_framework import generics

from .serializers import BehavioralTaskSerializer
from .models import BehavioralTask


class BehavioralTaskList(generics.ListCreateAPIView):
    serializer_class = BehavioralTaskSerializer

    def get_queryset(self):
        queryset = BehavioralTask.objects.all()
        session = self.request.query_params.get("session", None)

        if session is not None:
            queryset = queryset.filter(session=session).order_by("task_sequence")
        return queryset
