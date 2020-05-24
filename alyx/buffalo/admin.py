# Register the modules to show up at the admin page https://server/admin
from django.contrib import admin
from django import forms

from django.urls import reverse
from django.utils.html import format_html

from subjects.models import Subject
from actions.models import Session, Weighing
from alyx.base import BaseAdmin
from .models import (
    Task,
    SessionTask,
    SubjectFood,
    Electrode,
    StartingPoint,
    STLFile,
    ChannelRecording,
    ProcessedRecording,
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


class BuffaloSubject(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"
    form = SubjectForm
    fields = [
        "nickname",
        "lab",
        "responsible_user",
        "birth_date",
        "sex",
        "description",
    ]
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

    list_display = ["session", "tasks", "session_tasks_details"]
    model = SessionTask

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

    def save_model(self, request, obj, form, change):
        all_tasks = form.cleaned_data["all_tasks"]
        session = form.cleaned_data["session"]
        date_time = form.cleaned_data["date_time"]
        general_comments = form.cleaned_data["general_comments"]
        dataset_type = form.cleaned_data["dataset_type"]
        task_sequence = form.cleaned_data["task_sequence"]
        task = form.cleaned_data["task"]

        if all_tasks:
            for t in all_tasks:
                if task != t:
                    session_task = SessionTask.objects.create(
                        session=session,
                        date_time=date_time,
                        general_comments=general_comments,
                        task_sequence=task_sequence,
                        task=t,
                    )
                    for d in dataset_type:
                        session_task.dataset_type.add(d)
        super().save_model(request, obj, form, change)

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
        "category",
        "reward_type",
        "maze_type",
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


class BuffaloChannelRecording(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"
    list_display = [
        "subject_recorded",
        "session",
        "session_task_",
        "alive",
        "number_of_cells",
        "stl_file",
    ]

    def session_task_(self, obj):
        session_task = SessionTask.objects.get(pk=obj.session_task.id)
        return session_task.task

    def subject_recorded(self, obj):
        session = Session.objects.get(pk=obj.session.id)

        return session.subject


class BuffaloSTLFile(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"


admin.site.register(Subject, BuffaloSubject)
admin.site.register(Session, BuffaloSession)
admin.site.register(Weighing, BuffaloWeight)
admin.site.register(SessionTask, BuffaloSessionTask)
admin.site.register(Task, BuffaloTask)
admin.site.register(SubjectFood, BuffaloSubjectFood)
admin.site.register(Electrode, BuffaloElectrode)
admin.site.register(StartingPoint)
admin.site.register(STLFile, BuffaloSTLFile)
admin.site.register(ChannelRecording, BuffaloChannelRecording)
admin.site.register(ProcessedRecording)
