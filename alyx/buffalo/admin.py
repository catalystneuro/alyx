# Register the modules to show up at the admin page https://server/admin
from datetime import datetime
from django.contrib import admin
from django import forms
from django.forms import BaseInlineFormSet, ModelForm

from django.urls import reverse
from django.utils.html import format_html

from django.shortcuts import redirect

import nested_admin

from subjects.models import Subject
from actions.models import Session, Weighing
from alyx.base import BaseAdmin
from misc.models import Lab
from .models import (
    Task,
    TaskCategory,
    Location,
    SessionTask,
    FoodType,
    Electrode,
    StartingPoint,
    STLFile,
    ChannelRecording,
    ProcessedRecording,
    BuffaloSubject,
    ElectrodeLog,
    BuffaloElectrodeSubject,
    BuffaloElectrodeLogSubject,
    Reward,
    Platform,
    FoodLog,
    BuffaloSession,
)
from .forms import (
    WeighingForm,
    SessionTaskForm,
    TaskForm,
    SubjectFoodLog,
    SubjectForm,
    SessionForm,
    TaskForm,
    TaskCategoryForm,
    ElectrodeForm,
    FoodTypeForm,
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
        "options",
    ]

    search_fields = [
        "nickname",
    ]

    def get_form(self, request, obj=None, **kwargs):
        form = super(BuffaloSubjectAdmin, self).get_form(request, obj, **kwargs)
        lab = Lab.objects.filter(name__icontains="buffalo").first()
        form.base_fields["lab"].initial = lab
        return form

    def link(self, url, name):
        link_code = '<a class="button" href="{url}">{name}</a>'
        return format_html(link_code, url=url, name=name)

    def daily_observations(self, obj):
        url = reverse("daily-observation", kwargs={"subject_id": obj.id})
        return self.link(url, "Daily observations")

    def add_session(self, obj):
        url = "/buffalo/buffalosession/add/?subject=" + str(obj.id)
        return self.link(url, "Add Session")

    def set_electrodes(self, obj):
        url = reverse("admin:buffalo_buffaloelectrodesubject_change", args=[obj.id])
        return self.link(url, "Set electrodes")

    def new_electrode_logs(self, obj):
        url = reverse("admin:buffalo_buffaloelectrodelogsubject_change", args=[obj.id])
        return self.link(url, "New electrode logs")
    
    def set_electrodes_file(self, obj):
        url = reverse("electrode-bulk-load", kwargs={"subject_id": obj.id})
        return self.link(url, "Set electrodes form")

    def options(self, obj):
        select = "{} {} {} {} {}"
        select = select.format(
            self.daily_observations(obj),
            self.add_session(obj),
            self.set_electrodes(obj),
            self.new_electrode_logs(obj),
            self.set_electrodes_file(obj),
        )
        return format_html(select)


class ChannelRecordingFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(ChannelRecordingFormset, self).__init__(*args, **kwargs)


class ChannelRecordingInline(admin.TabularInline):
    model = ChannelRecording
    formset = ChannelRecordingFormset
    fields = ("electrode", "riples", "alive", "number_of_cells", "notes")
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "electrode":
            try:
                session = Session.objects.get(
                    pk=request.resolver_match.kwargs["object_id"]
                )
                kwargs["queryset"] = Electrode.objects.filter(subject=session.subject)
            except KeyError:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SessionTaskFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(SessionTaskFormset, self).__init__(*args, **kwargs)


class SessionTaskInline(admin.TabularInline):
    model = SessionTask
    formset = SessionTaskFormset
    fields = ("task", "session", "task_sequence", "dataset_type", "general_comments")
    extra = 0


def TemplateInitialDataAddChannelRecording(data, num_forms):
    class AlwaysChangedModelForm(ModelForm):
        def has_changed(self):
            """ Should returns True if data differs from initial.
            By always returning true even unchanged inlines will get validated and saved."""
            return True

    class AddChannelRecordingInline(admin.TabularInline):
        form = AlwaysChangedModelForm

        def get_queryset(self, request):
            self.request = request
            return ChannelRecording.objects.none()

        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            subject = request.GET.get("subject", None)
            if db_field.name == "electrode" and subject is not None:
                try:
                    kwargs["queryset"] = Electrode.objects.filter(subject=subject)
                except KeyError:
                    pass
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        class AddChannelRecordingFormset(BaseInlineFormSet):
            def __init__(self, *args, **kwargs):
                kwargs["initial"] = data
                for f in self.form.base_fields:
                    self.form.base_fields[f].widget.attrs["readonly"] = True
                super(
                    AddChannelRecordingInline.AddChannelRecordingFormset, self
                ).__init__(*args, **kwargs)

        model = ChannelRecording
        extra = num_forms
        fields = ("electrode", "riples", "alive", "number_of_cells", "notes")
        formset = AddChannelRecordingFormset

    return AddChannelRecordingInline


class BuffaloSubjectFood(admin.ModelAdmin):
    form = SubjectFoodLog
    change_form_template = "buffalo/change_form.html"
    list_display = ["subject", "session_", "amount", "date_time"]
    source = ""

    def session_(self, obj):
        try:
            BuffaloSession.objects.get(pk=obj.session.id)
            url = reverse("session-details", kwargs={"session_id": obj.session.id})
        except AttributeError:
            return "-"

        return format_html(
            '<a href="{url}">{name}</a>', url=url, name="Session Task Details"
        )

    def add_view(self, request, *args, **kwargs):
        try:
            if "daily" in request.environ["HTTP_REFERER"]:
                self.source = "daily"
        except KeyError:
            pass
        return super(BuffaloSubjectFood, self).add_view(request, *args, **kwargs)

    def response_add(self, request, obj):
        response = super(BuffaloSubjectFood, self).response_add(request, obj)
        if self.source == "daily":
            response["location"] = "/daily-observation/" + str(obj.subject_id)
            self.source = ""
        return response


class AlwaysChangedFoodForm(ModelForm):
    def has_changed(self):
        """ Should returns True if data differs from initial.
        By always returning true even unchanged inlines will get validated and saved."""
        return True

    def __init__(self, *args, **kwargs):
        super(AlwaysChangedFoodForm, self).__init__(*args, **kwargs)
        self.fields["food"].required = True
        self.fields["food"].help_text = "This fiels is required"
        self.fields["amount"].required = True
        self.fields["amount"].help_text = "Min value is 0"
        self.fields["amount"].error_messages["required"] = "Min value is 0"


class SessionFoodInline(admin.TabularInline):
    model = FoodLog
    form = AlwaysChangedFoodForm
    fields = ("session", "food", "amount")
    extra = 0
    min_num = 1
    can_delete = False


class BuffaloSessionAdmin(admin.ModelAdmin):
    form = SessionForm
    change_list_template = "buffalo/change_list.html"
    change_form_template = "buffalo/change_form.html"
    source = ""
    extra = 0

    list_display = [
        "name",
        "subject",
        "session_tasks",
        "narrative",
        "session_details",
        "start_time",
        "end_time",
    ]
    inlines = [SessionFoodInline, SessionTaskInline, ChannelRecordingInline]
    ordering = ("-start_time",)

    def get_form(self, request, obj=None, **kwargs):
        form = super(BuffaloSessionAdmin, self).get_form(request, obj, **kwargs)
        subject = request.GET.get("subject", None)
        lab = Lab.objects.filter(name__icontains="buffalo").first()
        form.base_fields["lab"].initial = lab
        form.base_fields["users"].initial = [request.user]

        if subject is not None:
            subject = BuffaloSubject.objects.get(pk=subject)
            session_name = f"{datetime.today().isoformat()}_{subject.nicknamesafe()}"
            form.base_fields["name"].initial = session_name
        return form

    def get_inline_instances(self, request, obj=None):
        subject = request.GET.get("subject", None)
        if subject is not None:
            prev_session = Session.objects.filter(subject=subject).order_by(
                "-start_time"
            )
            if prev_session:
                prev_channels = ChannelRecording.objects.filter(
                    session=prev_session[0].id,
                )
                initial = []
                for prev_channel in prev_channels:
                    initial.append(
                        {
                            "electrode": prev_channel.electrode,
                            "riples": prev_channel.riples,
                            "alive": prev_channel.alive,
                            "number_of_cells": prev_channel.number_of_cells,
                            "notes": prev_channel.notes,
                        }
                    )
                inlines = [
                    SessionFoodInline,
                    SessionTaskInline,
                    TemplateInitialDataAddChannelRecording(initial, len(initial)),
                ]
                inlines = [inline(self.model, self.admin_site) for inline in inlines]
                return inlines
        return super(BuffaloSessionAdmin, self).get_inline_instances(request, obj)

    def session_tasks(self, obj):
        tasks = SessionTask.objects.filter(session=obj.id)
        tasks_list = []
        for task in tasks:
            tasks_list.append(task.task)
        return tasks_list

    def session_details(self, obj):
        url = reverse("session-details", kwargs={"session_id": obj.id})
        return format_html(
            '<a href="{url}">{name}</a>', url=url, name="Session Details"
        )

    def add_view(self, request, *args, **kwargs):
        try:
            if "daily" in request.environ["HTTP_REFERER"]:
                self.source = "daily"
        except KeyError:
            pass
        return super(BuffaloSessionAdmin, self).add_view(request, *args, **kwargs)

    def response_add(self, request, obj):
        response = super(BuffaloSessionAdmin, self).response_add(request, obj)

        response["location"] = "/session-details/" + str(obj.id)
        return response

    def response_change(self, request, obj):
        response = super(BuffaloSessionAdmin, self).response_add(request, obj)
        response["location"] = "/session-details/" + str(obj.id)

        return response

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        try:
            if "session-details" in request.META["HTTP_REFERER"]:
                extra_context.update({"channels": 1})
        except KeyError:
            pass
        return super().change_view(
            request, object_id, form_url, extra_context=extra_context,
        )

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()

        for instance in instances:
            if isinstance(instance, ChannelRecording):
                if instance.electrode is not None:
                    instance.save()
                else:
                    continue
            instance.save()
        formset.save_m2m()


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

    def get_form(self, request, obj=None, **kwargs):
        form = super(BuffaloWeight, self).get_form(request, obj, **kwargs)
        subject = request.GET.get("subject", None)
        if subject is not None:
            subject = BuffaloSubject.objects.get(pk=subject)
            form.base_fields["subject"].initial = subject
        return form

    def weight_in_Kg(self, obj):
        url = f"/actions/weighing/{obj.id}/change"
        name = f"{obj.weight} kg"
        return format_html('<a href="{url}">{name}</a>', url=url, name=name)

    def add_view(self, request, *args, **kwargs):
        try:
            if "daily" in request.environ["HTTP_REFERER"]:
                self.source = "daily"
        except KeyError:
            pass
        return super(BuffaloWeight, self).add_view(request, *args, **kwargs)

    def response_add(self, request, obj):
        response = super(BuffaloWeight, self).response_add(request, obj)
        if self.source == "daily":
            response["location"] = "/daily-observation/" + str(obj.subject_id)
            self.source = ""
        return response


class BuffaloSessionTask(admin.ModelAdmin):
    form = SessionTaskForm
    change_form_template = "buffalo/change_form.html"

    def get_queryset(self, request):
        qs = super(BuffaloSessionTask, self).get_queryset(request).distinct("session")
        return qs

    list_display = ["task_details", "tasks", "general_comments", "session_details"]
    model = SessionTask

    def task_details(self, obj):
        if obj.session is None:
            return ""
        return obj.session.name

    def session_details(self, obj):
        try:
            url = reverse("session-details", kwargs={"session_id": obj.session.id})
        except AttributeError:
            url = ""

        return format_html(
            '<a href="{url}">{name}</a>', url=url, name="Session Details"
        )

    def tasks(self, obj):
        tasks = SessionTask.objects.filter(session=obj.session)
        tasks_list = []
        for task in tasks:
            tasks_list.append(task.task)
        return tasks_list

    ordering = ("session",)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class BuffaloTask(admin.ModelAdmin):
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
    ordering = ("-updated",)

    def name_version(self, obj):
        version = f" (version:{obj.version})"
        return obj.name + version

    def new_version(self, obj):
        if obj.first_version is True:
            url = reverse("buffalo-task-version", kwargs={"pk": obj.id})
            return format_html(
                '<a href="{url}">{name}</a>', url=url, name="Add new version"
            )

        return ""

    def dataset_type_name(self, obj):
        return "\n".join([d.name for d in obj.dataset_type.all()])

    def save_model(self, request, obj, form, change):
        if change is False and obj.first_version is True:
            obj.version = "1"
        if change:
            saved_version = Task.objects.get(pk=obj.id)
            obj.name = saved_version.name
            obj.version = saved_version.version

        super().save_model(request, obj, form, change)


class StartingPointFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(StartingPointFormset, self).__init__(*args, **kwargs)


class StartingPointInline(nested_admin.NestedTabularInline):
    model = StartingPoint
    formset = StartingPointFormset
    fields = ("electrode", "x", "y", "z", "x_norm", "y_norm", "z_norm", "depth", "date_time", "notes")
    extra = 0


class BuffaloElectrode(nested_admin.NestedTabularInline):
    model = Electrode
    fields = ("channel_number", "turns_per_mm", "millimeters", "date_time", "notes")
    extra = 0
    inlines = [StartingPointInline]


class BuffaloElectrodeSubjectAdmin(nested_admin.NestedModelAdmin):
    change_form_template = "buffalo/change_form.html"
    form = SubjectForm

    list_display = [
        "nickname",
        "birth_date",
        "sex",
        "description",
        "responsible_user",
    ]

    fields = ["nickname", "unique_id", "name"]

    search_fields = [
        "nickname",
    ]

    inlines = [BuffaloElectrode]

    def response_change(self, request, obj):
        return redirect("/buffalo/buffalosubject")

    def has_add_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("nickname", "unique_id", "name")
        return self.readonly_fields


def TemplateInitialDataElectrodeLog(data, num_forms, subject_id):
    class BuffaloElectrodeLog(admin.TabularInline):
        def get_queryset(self, request):
            self.request = request
            return ElectrodeLog.objects.none()

        class ElectrodeLogInlineFormSet(BaseInlineFormSet):
            def __init__(self, *args, **kwargs):
                kwargs["initial"] = data
                super(BuffaloElectrodeLog.ElectrodeLogInlineFormSet, self).__init__(
                    *args, **kwargs
                )
                for form in self:
                    form.fields["electrode"].queryset = Electrode.objects.prefetch_related('subject').filter(subject=subject_id)


        model = ElectrodeLog
        extra = num_forms
        fields = ("electrode", "turn", "impedance", "date_time", "notes")
        formset = ElectrodeLogInlineFormSet

    return BuffaloElectrodeLog


class BuffaloElectrodeLogSubjectAdmin(admin.ModelAdmin):

    change_form_template = "buffalo/change_form.html"
    form = SubjectForm
    list_display = [
        "nickname",
        "birth_date",
        "sex",
        "description",
        "responsible_user",
    ]
    fields = ["nickname", "unique_id", "name"]
    search_fields = [
        "nickname",
    ]

    def get_inline_instances(self, request, obj=None):
        electrodes = Electrode.objects.filter(subject=obj.id)
        initial = []
        for electrode in electrodes:
            initial.append({"electrode": electrode.id})
        inlines = [TemplateInitialDataElectrodeLog(initial, len(initial), obj.id)]
        return [inline(self.model, self.admin_site) for inline in inlines]

    def response_change(self, request, obj):
        return redirect("/buffalo/buffalosubject")

    def has_add_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ("nickname", "unique_id", "name")
        return self.readonly_fields


class BuffaloElectrodeLogAdmin(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"
    form = ElectrodeForm
    list_display = ["subject", "electrode", "turn", "impedance", "current_location", "date_time"]
    fields = ("subject", "electrode", "turn", "impedance", "date_time", "notes")
    search_fields = [
        "subject__nickname",
    ]
    ordering = ["-date_time"]


class BuffaloChannelRecording(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"
    list_display = [
        "subject_recorded",
        "session_",
        "alive",
        "number_of_cells",
    ]

    def session_(self, obj):
        if obj.session is None:
            return ""
        return obj.session.name

    def subject_recorded(self, obj):
        if obj.session is None:
            return ""
        session = Session.objects.get(pk=obj.session.id)
        return session.subject


class BuffaloSTLFile(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"


class BuffaloStartingPoint(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"


class BuffaloCategory(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"
    form = TaskCategoryForm


class FoodTypeAdmin(admin.ModelAdmin):
    form = FoodTypeForm

    def has_delete_permission(self, request, obj=None):
        if "buffalo/buffalosession" in request.path:
            return False
        return True


admin.site.register(BuffaloSubject, BuffaloSubjectAdmin)
admin.site.register(BuffaloElectrodeSubject, BuffaloElectrodeSubjectAdmin)
admin.site.register(BuffaloElectrodeLogSubject, BuffaloElectrodeLogSubjectAdmin)
admin.site.register(ElectrodeLog, BuffaloElectrodeLogAdmin)
admin.site.register(BuffaloSession, BuffaloSessionAdmin)
admin.site.register(Weighing, BuffaloWeight)
admin.site.register(SessionTask, BuffaloSessionTask)
admin.site.register(Task, BuffaloTask)
admin.site.register(FoodLog, BuffaloSubjectFood)
admin.site.register(StartingPoint, BuffaloStartingPoint)
admin.site.register(STLFile, BuffaloSTLFile)
admin.site.register(ChannelRecording, BuffaloChannelRecording)
admin.site.register(ProcessedRecording)
admin.site.register(TaskCategory, BuffaloCategory)
admin.site.register(Location)
admin.site.register(Reward)
admin.site.register(Platform)
admin.site.register(FoodType, FoodTypeAdmin)
