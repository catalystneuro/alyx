from datetime import datetime
from django import forms
import django.forms
from django.forms import ModelForm

from actions.models import Session, Weighing

# from subjects.models import Subject
from .models import (
    Task,
    DailyObservation,
    SessionTask,
    SubjectFood,
    BuffaloSubject,
    ChannelRecording,
    Electrode,
)


class TaskForm(forms.ModelForm):
    name = forms.CharField(label="Task name", required=True, max_length=150)
    description = forms.CharField(label="Description (optional)", required=False)

    class Meta:
        name = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
        model = Task
        fields = [
            "name",
            "description",
            "training",
            "platform",
            "category",
            "reward",
            "location",
            "dataset_type",
        ]


class TaskVersionForm(forms.ModelForm):
    name = forms.CharField(label="Task name", required=True, max_length=150)

    def __init__(self, *args, **kwargs):
        super(TaskVersionForm, self).__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["readonly"] = True

    class Meta:
        name = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
        model = Task
        fields = [
            "name",
            "description",
            "category",
            "version",
            "original_task",
            "first_version",
        ]
        widgets = {
            "version": forms.HiddenInput(),
            "original_task": forms.HiddenInput(),
            "first_version": forms.HiddenInput(),
        }


class DailyObservationForm(ModelForm):
    class Meta:
        model = DailyObservation
        fields = ["subject", "date_time", "run", "food", "general_comments"]


class SubjectForm(ModelForm):
    nickname = forms.CharField(label="Name", required=True, max_length=150)
    code = forms.CharField(label="Code", required=False, max_length=150)

    class Meta:
        model = BuffaloSubject
        fields = [
            "nickname",
            "unique_id",
            "code",
            "lab",
            "responsible_user",
            "birth_date",
            "sex",
            "description",
        ]


class SessionForm(ModelForm):
    name = forms.CharField(
        label="Session name",
        required=False,
        max_length=150,
        initial=datetime.today().strftime("%d/%m/%Y"),
        widget=forms.TextInput(attrs={"readonly": "readonly"}),
    )

    subject = forms.ModelChoiceField(
        queryset=BuffaloSubject.objects.all(), required=False
    )

    class Meta:
        model = Session
        fields = [
            "name",
            "subject",
            "users",
            "lab",
            "narrative",
            "start_time",
            "end_time",
        ]


class CustomModelChoiceField(django.forms.ModelChoiceField):
    """Subclasses Django's ModelChoiceField and adds one parameter, `obj_label`.
        This should be a callable with one argument (the current object) which
        returns a string to use as the label of that object or instance."""

    def __init__(self, obj_label=None, *args, **kwargs):
        super(CustomModelChoiceField, self).__init__(*args, **kwargs)
        self.obj_label = obj_label

    def label_from_instance(self, obj):
        # import pdb; pdb.set_trace()
        if self.obj_label:
            return self.label(obj.name)
        return super(CustomModelChoiceField, self).label_from_instance(obj.name)


class TaskSessionForm(ModelForm):
    task = forms.ModelMultipleChoiceField(queryset=Task.objects.all())
    session = CustomModelChoiceField(queryset=Session.objects.all())

    class Meta:
        model = SessionTask
        fields = [
            "task",
            "session",
            "date_time",
            "dataset_type",
            "general_comments",
            "task_sequence",
        ]


class WeighingForm(forms.ModelForm):
    subject = forms.ModelChoiceField(
        queryset=BuffaloSubject.objects.all(), required=False
    )
    weight = forms.FloatField(help_text="Weight in Kg")

    def __init__(self, *args, **kwargs):
        super(WeighingForm, self).__init__(*args, **kwargs)
        self.fields["weight"].widget.attrs = {"min": 0, "max": 35}

    class Meta:
        model = Weighing
        fields = ["subject", "date_time", "weight", "user"]


class SubjectFoodForm(forms.ModelForm):
    subject = forms.ModelChoiceField(
        queryset=BuffaloSubject.objects.all(), required=False
    )
    amount = forms.FloatField(help_text="in Ml")

    def __init__(self, *args, **kwargs):
        super(SubjectFoodForm, self).__init__(*args, **kwargs)
        self.fields["amount"].widget.attrs = {"min": 50, "max": 1500}

    class Meta:
        model = SubjectFood
        fields = [
            "subject",
            "amount",
            "date_time",
        ]
