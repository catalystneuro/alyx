from datetime import datetime, date
from django import forms
import django.forms
from django.forms import ModelForm
from django.core.validators import FileExtensionValidator

from .utils import (
    validate_mat_file,
    validate_electrodelog_file,
    validate_channel_recording_file,
    validate_sessions_file,
)


from .models import (
    Task,
    SessionTask,
    BuffaloSubject,
    Electrode,
    TaskCategory,
    FoodType,
    FoodLog,
    BuffaloSession,
    WeighingLog,
    STLFile,
    StartingPointSet,
    NeuralPhenomena,
    Device,
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


class ElectrodeLogSubjectForm(ModelForm):
    nickname = forms.CharField(label="Name", required=True, max_length=150)
    code = forms.CharField(label="Code", required=False, max_length=150)
    prior_order = forms.BooleanField(
        required=False,
        help_text="Save logs based on the order. It takes the first changed \
            row datetime like base and add one second between records.",
        label="Prioritize order",
    )

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
        widgets = {
            "lab": forms.HiddenInput(),
        }


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

    def clean(self):
        cleaned_data = super().clean()
        needs_review = cleaned_data.get("needs_review")
        narrative = cleaned_data.get("narrative")
        if needs_review and not narrative:
            raise forms.ValidationError(
                "This session needs review. Please add data to 'Narrative'."
            )

    class Meta:
        model = BuffaloSession
        fields = [
            "name",
            "subject",
            "users",
            "unknown_user",
            "lab",
            "needs_review",
            "narrative",
            "pump_setting",
            "chamber_cleaning",
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
            "needs_review",
            "general_comments",
            "json",
            "task_sequence",
        ]


class SubjectWeighingForm(forms.ModelForm):
    subject = forms.ModelChoiceField(
        queryset=BuffaloSubject.objects.all(), required=False
    )
    weight = forms.FloatField(help_text="Weight in Kg")

    def __init__(self, *args, **kwargs):
        super(SubjectWeighingForm, self).__init__(*args, **kwargs)
        self.fields["weight"].widget.attrs = {"min": 0, "max": 35}

    class Meta:
        model = WeighingLog
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
        max_length=1024, help_text='{"env": ["env1", "env2"]}', required=False
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
    file = forms.FileField(validators=[FileExtensionValidator(["mat"])])
    structure_name = forms.CharField(
        label="Structure name", required=False, max_length=250
    )
    device = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        device_id = cleaned_data.get("device")
        structure = cleaned_data.get("structure_name")
        if structure:
            validate_mat_file(file, structure)
        else:
            device = Device.objects.get(pk=device_id)
            validate_mat_file(file, device.subject.nickname)


class ElectrodeLogBulkLoadForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(["xlsm"])])
    device = forms.ModelChoiceField(queryset=Device.objects.none())
    subject = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        validate_electrodelog_file(file)

    def __init__(self, *args, **kwargs):
        subject_id = kwargs.pop("subject_id", None)
        if subject_id is None and "subject" in kwargs["initial"].keys():
            subject_id = kwargs["initial"]["subject"]
        super(ElectrodeLogBulkLoadForm, self).__init__(*args, **kwargs)
        self.fields["device"].queryset = Device.objects.filter(subject=subject_id)


class ChannelRecordingBulkLoadForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(["xlsx"])])
    device = forms.ModelChoiceField(queryset=Device.objects.none())
    sufix = forms.CharField(
        label="Sufix (Ex. a)", required=False, max_length=250
    )
    subject = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        validate_channel_recording_file(file)

    def __init__(self, *args, **kwargs):
        subject_id = kwargs.pop("subject_id", None)
        if subject_id is None and "subject" in kwargs["initial"].keys():
            subject_id = kwargs["initial"]["subject"]
        super(ChannelRecordingBulkLoadForm, self).__init__(*args, **kwargs)
        self.fields["device"].queryset = Device.objects.filter(subject=subject_id)


class PlotFilterForm(forms.Form):
    cur_year = datetime.today().year
    year_range = tuple([i for i in range(cur_year - 2, cur_year + 10)])

    stl = forms.ModelChoiceField(queryset=StartingPointSet.objects.none())
    starting_point_set = forms.ModelChoiceField(queryset=STLFile.objects.none())
    date = forms.DateField(initial=date.today)
    download_points = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        subject_id = kwargs.pop("subject_id")
        super(PlotFilterForm, self).__init__(*args, **kwargs)
        self.fields["stl"].queryset = STLFile.objects.filter(subject=subject_id)
        self.fields["starting_point_set"].queryset = StartingPointSet.objects.filter(
            subject=subject_id
        )


class SessionQueriesForm(forms.Form):
    cur_year = datetime.today().year
    year_range = tuple([i for i in range(cur_year - 2, cur_year + 10)])

    stl = forms.ModelChoiceField(queryset=StartingPointSet.objects.none())
    starting_point_set = forms.ModelChoiceField(queryset=STLFile.objects.none())
    task = forms.ModelChoiceField(queryset=SessionTask.objects.none())
    is_in_stl = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):

        subject_id = kwargs.pop("subject_id")
        super(SessionQueriesForm, self).__init__(*args, **kwargs)
        self.fields["stl"].queryset = STLFile.objects.filter(subject=subject_id)
        self.fields["starting_point_set"].queryset = StartingPointSet.objects.filter(
            subject=subject_id
        )
        session_tasks = SessionTask.objects.filter(session__subject=subject_id).values(
            "task"
        )
        self.fields["task"].queryset = Task.objects.filter(id__in=session_tasks)


class SessionsLoadForm(forms.Form):
    file = forms.FileField(validators=[FileExtensionValidator(["xlsx"])])
    subject = forms.CharField(widget=forms.HiddenInput())

    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("file")
        file_name = file.name.split(".")[0]
        subject = BuffaloSubject.objects.get(pk=cleaned_data.get("subject"))
        if file_name.lower() != subject.nickname.lower():
            raise forms.ValidationError(
                "The file name is different than the subject's nickname"
            )

        validate_sessions_file(file)


class NeuralPhenomenaForm(forms.ModelForm):
    class Meta:
        model = NeuralPhenomena
        fields = [
            "name",
            "description",
        ]
