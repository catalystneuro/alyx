from rest_framework import viewsets
from rest_framework import generics, permissions

from .serializers import BehavioralTaskSerializer
from .models import BehavioralTask


class BehavioralTaskListSerializer(generics.ListCreateAPIView):
    queryset = BehavioralTask.objects.all().order_by('name')
    serializer_class = BehavioralTaskSerializer
