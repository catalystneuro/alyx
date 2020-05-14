from django import forms
from django.forms import ModelForm

from actions.models import Session
from subjects.models import Subject
from .models import Task, DailyObservation, SessionTask


class TaskForm(ModelForm):
    name = forms.CharField(label="Task name", required=True, max_length=150)

    class Meta:
        model = Task
        fields = ["name", "description", "category", "reward_type", "maze_type"]


class DailyObservationForm(ModelForm):
    class Meta:
        model = DailyObservation
        fields = ["subject", "run", "food", "general_comments"]


class SubjectForm(ModelForm):
    nickname = forms.CharField(label="Name", required=True, max_length=150)
    # lab = forms.ChoiceField(widget = forms.HiddenInput(), choices = ([('buffalo', 'Buffalo')]), initial='buffalo', required = True,)
    class Meta:
        model = Subject
        fields = [
            "nickname",
            "lab",
            "responsible_user",
            "birth_date",
            "sex",
            "description",
        ]


class SessionForm(ModelForm):
    name = forms.CharField(label="Session name", required=False, max_length=150)

    class Meta:
        model = Session
        fields = ["name", "subject", "users", "lab", "start_time", "end_time"]


class TaskSessionForm(ModelForm):
    class Meta:
        model = SessionTask
        fields = [
            "task",
            "session",
            "dataset_type",
            "general_comments",
            "task_sequence",
        ]
