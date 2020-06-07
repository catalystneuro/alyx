from datetime import datetime
from django import forms
import django.forms
from django.forms import ModelForm
from django.core.validators import FileExtensionValidator
from .utils import validate_mat_file

from actions.models import Weighing


from .models import (
    Task,
    SessionTask,
    BuffaloSubject,
    ChannelRecording,
    Electrode,
    TaskCategory,
    FoodType,
    FoodLog,
    BuffaloSession,
)


class TaskForm(forms.ModelForm):
    name = forms.CharField(label="Task name", required=True, max_length=150)
    description = forms.CharField(label="Description (optional)", required=False)

    class Meta:
        name = forms.CharField(widget=forms.TextInput(attrs={"readonly": "readonly"}))
        model = Task
        fields = [
            "name",
            "version",
            "description",
            "training",
            "platform",
            "category",
            "json",
            "reward",
            "location",
            "dataset_type",
        ]
        widgets = {
            "version": forms.HiddenInput(),
        }


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
            "version",
            "description",
            "training",
            "platform",
            "category",
            "json",
            "reward",
            "location",
            "original_task",
            "first_version",
        ]
        widgets = {
            "version": forms.HiddenInput(),
            "original_task": forms.HiddenInput(),
            "first_version": forms.HiddenInput(),
        }


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
        max_length=250,
        initial=datetime.today().isoformat(),
        widget=forms.TextInput(attrs={"readonly": "readonly", "size": "40"}),
    )

    subject = forms.ModelChoiceField(
        queryset=BuffaloSubject.objects.all(), required=True
    )

    class Meta:
        model = BuffaloSession
        fields = [
            "name",
            "subject",
            "users",
            "lab",
            "dataset_type",
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
        if self.obj_label:
            return self.label(obj.name)
        return super(CustomModelChoiceField, self).label_from_instance(obj.name)


class SessionTaskForm(ModelForm):
    session = CustomModelChoiceField(queryset=BuffaloSession.objects.all())

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


class SubjectFoodLog(forms.ModelForm):
    subject = forms.ModelChoiceField(
        queryset=BuffaloSubject.objects.all(), required=False
    )

    def __init__(self, *args, **kwargs):
        super(SubjectFoodLog, self).__init__(*args, **kwargs)
        self.fields["amount"].widget.attrs = {"min": 50, "max": 1500}

    class Meta:
        model = FoodLog
        fields = [
            "subject",
            "food",
            "amount",
            "date_time",
        ]


class TaskCategoryForm(forms.ModelForm):
    json = forms.CharField(
        max_length=1024, help_text='{"env": "env value"}', required=False
    )

    class Meta:
        model = TaskCategory
        fields = [
            "name",
            "json",
        ]


class ElectrodeForm(forms.ModelForm):
    subject = forms.ModelChoiceField(
        queryset=BuffaloSubject.objects.all(), required=False
    )

    class Meta:
        model = Electrode
        fields = [
            "subject",
            "date_time",
            "millimeters",
            "channel_number",
            "notes",
        ]


class FoodTypeForm(forms.ModelForm):
    class Meta:
        model = FoodType
        fields = [
            "name",
            "unit",
        ]
class ElectrodeBulkLoadForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(['mat'])])
    subject = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        subject_id = cleaned_data.get("subject")
        subject = BuffaloSubject.objects.get(pk=subject_id)
        validate_mat_file(file, subject.unique_id)

