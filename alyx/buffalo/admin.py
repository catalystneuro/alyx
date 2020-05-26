# Register the modules to show up at the admin page https://server/admin
from django.contrib import admin
from django import forms
from django.forms import BaseInlineFormSet

from django.urls import reverse
from django.utils.html import format_html

from subjects.models import Subject
from actions.models import Session, Weighing
from alyx.base import BaseAdmin
from .models import (
    Task,
    TaskCategory,
    Location,
    SessionTask,
    SubjectFood,
    Electrode,
    StartingPoint,
    STLFile,
    ChannelRecording,
    ProcessedRecording,
    ElectrodeTurn,
    BuffaloSubject,
    Reward,
)
from .forms import (
    WeighingForm,
    TaskSessionForm,
    TaskForm,
    SubjectFoodForm,
    SubjectForm,
    SessionForm,
    TaskForm,
)


class BuffaloSubjectAdmin(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"
    form = SubjectForm

    list_display = [
        "nickname",
        "birth_date",
        "sex",
        "description",
        "responsible_user",
        "daily_observations",
    ]

    search_fields = [
        "nickname",
    ]

    def daily_observations(self, obj):
        url = reverse("daily-observation", kwargs={"subject_id": obj.id})
        return format_html('<a href="{url}">{name}</a>', url=url, name="See More")


class ChannelRecordingFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(ChannelRecordingFormset, self).__init__(*args, **kwargs)


class ChannelRecordingInline(admin.TabularInline):
    model = ChannelRecording
    formset = ChannelRecordingFormset
    fields = ("electrode", "alive", "notes")
    extra = 1


class SessionTaskFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(SessionTaskFormset, self).__init__(*args, **kwargs)


class SessionTaskInline(admin.TabularInline):
    model = SessionTask
    formset = SessionTaskFormset
    fields = ("task", "session", "task_sequence", "dataset_type", "general_comments")
    extra = 1


class BuffaloSession(admin.ModelAdmin):
    form = SessionForm
    change_list_template = "buffalo/change_list.html"
    change_form_template = "buffalo/change_form.html"
    source = ""

    list_display = [
        "name",
        "subject",
        "session_tasks",
        "narrative",
        "session_details",
        "start_time",
        "end_time",
    ]
    inlines = [SessionTaskInline]

    def session_tasks(self, obj):
        tasks = SessionTask.objects.filter(session=obj.id)
        tasks_list = []
        for task in tasks:
            tasks_list.append(task.task)
        return tasks_list

    def session_details(self, obj):
        url = reverse("session-tasks", kwargs={"session_id": obj.id})
        return format_html(
            '<a href="{url}">{name}</a>', url=url, name="Session Task Details"
        )

    def add_view(self, request, *args, **kwargs):
        if "daily" in request.environ["HTTP_REFERER"]:
            self.source = "daily"
        return super(BuffaloSession, self).add_view(request, *args, **kwargs)

    def response_add(self, request, obj):
        response = super(BuffaloSession, self).response_add(request, obj)
        if self.source == "daily":
            response["location"] = "/daily-observation/" + str(obj.subject_id)
            self.source = ""
        return response


class BuffaloWeight(BaseAdmin):
    form = WeighingForm
    change_form_template = "buffalo/change_form.html"
    source = ""

    list_display = [
        "subject",
        "weight_in_Kg",
        "user",
        "date_time",
    ]

    def weight_in_Kg(self, obj):
        url = f"/actions/weighing/{obj.id}/change"
        name = f"{obj.weight} kg"
        return format_html('<a href="{url}">{name}</a>', url=url, name=name)

    def add_view(self, request, *args, **kwargs):
        if "daily" in request.environ["HTTP_REFERER"]:
            self.source = "daily"
        return super(BuffaloWeight, self).add_view(request, *args, **kwargs)

    def response_add(self, request, obj):
        response = super(BuffaloWeight, self).response_add(request, obj)
        if self.source == "daily":
            response["location"] = "/daily-observation/" + str(obj.subject_id)
            self.source = ""
        return response


class BuffaloSessionTask(admin.ModelAdmin):
    form = TaskSessionForm
    change_form_template = "buffalo/change_form.html"

    def get_queryset(self, request):
        qs = super(BuffaloSessionTask, self).get_queryset(request).distinct("session")
        return qs

    list_display = ["session_", "tasks", "session_tasks_details"]
    model = SessionTask

    def session_(self, obj):
        return obj.session.name

    def session_tasks_details(self, obj):
        try:
            url = reverse("session-tasks", kwargs={"session_id": obj.session.id})
        except AttributeError:
            url = ""

        return format_html(
            '<a href="{url}">{name}</a>', url=url, name="Session Task Details"
        )

    def tasks(self, obj):
        tasks = SessionTask.objects.filter(session=obj.session)
        tasks_list = []
        for task in tasks:
            tasks_list.append(task.task)
        return tasks_list

    ordering = ("session",)


class BuffaloSubjectFood(admin.ModelAdmin):
    form = SubjectFoodForm
    change_form_template = "buffalo/change_form.html"
    list_display = ["subject", "amount", "date_time"]
    source = ""

    def add_view(self, request, *args, **kwargs):
        if "daily" in request.environ["HTTP_REFERER"]:
            self.source = "daily"
        return super(BuffaloSubjectFood, self).add_view(request, *args, **kwargs)

    def response_add(self, request, obj):
        response = super(BuffaloSubjectFood, self).response_add(request, obj)
        if self.source == "daily":
            response["location"] = "/daily-observation/" + str(obj.subject_id)
            self.source = ""
        return response


class BuffaloTask(BaseAdmin):
    change_form_template = "buffalo/change_form.html"
    form = TaskForm
    list_display = [
        "name_version",
        "description",
        "training",
        "platform",
        "category",
        "reward",
        "location",
        "dataset_type_name",
        "new_version",
    ]
    ordering = ("name",)

    def name_version(self, obj):
        version = f" (version:{obj.version})"
        return obj.name + version

    def new_version(self, obj):
        if obj.version == "1":
            url = reverse("buffalo-task-version", kwargs={"pk": obj.id})
            return format_html(
                '<a href="{url}">{name}</a>', url=url, name="Add new version"
            )
        return ""

    def dataset_type_name(self, obj):
        return "\n".join([d.name for d in obj.dataset_type.all()])


class StartingPointFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(StartingPointFormset, self).__init__(*args, **kwargs)


class StartingPointInline(admin.TabularInline):
    model = StartingPoint
    formset = StartingPointFormset
    fields = ("electrode", "x", "y", "z", "lab_member", "depth", "date_time", "notes")
    extra = 1


class BuffaloElectrode(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"
    list_display = [
        "subject",
        "turn",
        "millimeters",
        "impedance",
        "units",
        "notes",
    ]
    inlines = [StartingPointInline]


class BuffaloChannelRecording(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"
    list_display = [
        "subject_recorded",
        "session_",
        "alive",
        "number_of_cells",
    ]

    def session_(self, obj):
        return obj.session.name

    def subject_recorded(self, obj):
        session = Session.objects.get(pk=obj.session.id)
        return session.subject


class BuffaloSTLFile(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"


class BuffaloStartingPoint(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"


admin.site.register(BuffaloSubject, BuffaloSubjectAdmin)
admin.site.register(Session, BuffaloSession)
admin.site.register(Weighing, BuffaloWeight)
admin.site.register(SessionTask, BuffaloSessionTask)
admin.site.register(Task, BuffaloTask)
admin.site.register(SubjectFood, BuffaloSubjectFood)
admin.site.register(Electrode, BuffaloElectrode)
admin.site.register(StartingPoint, BuffaloStartingPoint)
admin.site.register(STLFile, BuffaloSTLFile)
admin.site.register(ChannelRecording, BuffaloChannelRecording)
admin.site.register(ProcessedRecording)
admin.site.register(TaskCategory)
admin.site.register(Location)
admin.site.register(ElectrodeTurn)
admin.site.register(Reward)
