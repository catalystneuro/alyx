# Register the modules to show up at the admin page https://server/admin
from datetime import datetime, timedelta
from django.contrib import admin
from django import forms
from django.forms import BaseInlineFormSet, ModelForm
from django_admin_listfilter_dropdown.filters import (
    RelatedDropdownFilter,
    DropdownFilter,
)
from rangefilter.filter import DateRangeFilter
from django.urls import reverse
from django.utils.html import format_html
from django.shortcuts import redirect
from django.contrib import messages
from reversion.admin import VersionAdmin
import nested_admin

from actions.models import Session
from alyx.base import BaseAdmin
from misc.models import Lab
from alyx.base import DefaultListFilter
from data.admin import BaseExperimentalDataAdmin

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
    WeighingLog,
    BuffaloDataset,
    StartingPointSet,
)
from .forms import (
    SubjectWeighingForm,
    SessionTaskForm,
    TaskForm,
    SubjectFoodLog,
    SubjectForm,
    SessionForm,
    TaskCategoryForm,
    ElectrodeForm,
    FoodTypeForm,
    ElectrodeLogSubjectForm,
)


class BuffaloSubjectAdmin(BaseAdmin):
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
    ordering = ("-updated",)

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

    def add_stl(self, obj):
        url = "/buffalo/stlfile/add/?subject=" + str(obj.id)
        return self.link(url, "Add STL file")

    def set_electrodes(self, obj):
        url = reverse("admin:buffalo_buffaloelectrodesubject_change", args=[obj.id])
        return self.link(url, "Set electrodes")

    def new_electrode_logs(self, obj):
        url = reverse("admin:buffalo_buffaloelectrodelogsubject_change", args=[obj.id])
        return self.link(url, "New electrode logs")

    def set_electrodes_file(self, obj):
        url = reverse("electrode-bulk-load", kwargs={"subject_id": obj.id})
        return self.link(url, "Set electrodes form")

    def plots(self, obj):
        url = reverse("plots", kwargs={"subject_id": obj.id})
        return self.link(url, "View plots")

    def session_queries(self, obj):
        url = reverse("session-queries", kwargs={"subject_id": obj.id})
        return self.link(url, "Session queries")

    def load_sessions(self, obj):
        url = reverse("sessions-load", kwargs={"subject_id": obj.id})
        return self.link(url, "Load Sessions")

    def options(self, obj):
        select = "{} {} {} {} {} {} {} {} {}"
        select = select.format(
            self.daily_observations(obj),
            self.add_session(obj),
            self.add_stl(obj),
            self.set_electrodes(obj),
            self.new_electrode_logs(obj),
            self.set_electrodes_file(obj),
            self.plots(obj),
            self.session_queries(obj),
            self.load_sessions(obj),
        )
        return format_html(select)


class ChannelRecordingFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(ChannelRecordingFormset, self).__init__(*args, **kwargs)


class ChannelRecordingInline(nested_admin.NestedTabularInline):
    model = ChannelRecording
    formset = ChannelRecordingFormset
    fields = ("electrode", "ripples", "alive", "number_of_cells", "notes")
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
            try:
                subject = request.GET.get("subject", None)
                if subject is not None:
                    kwargs["queryset"] = Electrode.objects.filter(subject=subject)
            except:
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SessionTaskFormset(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(SessionTaskFormset, self).__init__(*args, **kwargs)

    def clean(self):
        super(SessionTaskFormset, self).clean()
        for form in self.forms:
            if form.cleaned_data.get("needs_review") and not form.cleaned_data.get(
                "general_comments"
            ):
                raise forms.ValidationError(
                    "A task needs review. Please add data to 'General Comments' for that task"
                )


class SessionDataNestedsetInline(nested_admin.NestedTabularInline):
    model = BuffaloDataset
    fields = ("session_task", "dataset_type", "collection", "file_name")
    extra = 0


class SessionTaskInline(nested_admin.NestedTabularInline):
    model = SessionTask
    formset = SessionTaskFormset
    fields = (
        "task",
        "session",
        "task_sequence",
        "needs_review",
        "general_comments",
        "json",
        "start_time",
    )
    extra = 0
    inlines = [SessionDataNestedsetInline]


def TemplateInitialDataAddChannelRecording(data, num_forms):
    class AlwaysChangedModelForm(ModelForm):
        def has_changed(self):
            """ Should returns True if data differs from initial.
            By always returning true even unchanged inlines will get validated and saved."""
            return True

    class AddChannelRecordingInline(nested_admin.NestedTabularInline):
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
        fields = ("electrode", "ripples", "alive", "number_of_cells", "notes")
        formset = AddChannelRecordingFormset

    return AddChannelRecordingInline


class BuffaloSubjectFood(BaseAdmin):
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

    def has_delete_permission(self, request, obj=None):
        try:
            if obj.session is not None or obj.subject is not None:
                return False
        except:
            return True

    def has_change_permission(self, request, obj=None):
        try:
            if obj.session is not None or obj.subject is not None:
                return False
        except:
            return True


class SessionFoodForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SessionFoodForm, self).__init__(*args, **kwargs)
        self.fields["food"].required = True
        self.fields["food"].help_text = "This fiels is required"
        self.fields["amount"].required = True
        self.fields["amount"].help_text = "Min value is 0"
        self.fields["amount"].error_messages["required"] = "Min value is 0"


class SessionFoodInline(nested_admin.NestedTabularInline):
    model = FoodLog
    form = SessionFoodForm
    fields = ("session", "food", "amount")
    extra = 0
    min_num = 1
    can_delete = False


class SessionWeighingForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SessionWeighingForm, self).__init__(*args, **kwargs)
        self.fields["weight"].required = False
        self.fields["weight"].widget.attrs = {"min": 0, "max": 35}
        self.fields["weight"].help_text = "Weight in Kg"


class SessionWeighingInline(nested_admin.NestedTabularInline):
    model = WeighingLog
    form = SessionWeighingForm
    fields = ("session", "weight")
    min_num = 1
    max_num = 1
    can_delete = False


class SessionTaskListFilter(DefaultListFilter):
    title = "Task"
    parameter_name = "task"

    def lookups(self, request, model_admin):
        sessions_tasks = set(
            [c.task for c in SessionTask.objects.filter(task__isnull=False)]
        )
        return [("all", "All")] + [(c.id, c) for c in sessions_tasks]

    def queryset(self, request, queryset):
        if self.value() == "all":
            return queryset.all()

        elif self.value() is not None:
            sessions = (
                SessionTask.objects.filter(task=self.value())
                .exclude(session=None)
                .values_list("session")
            )
            return queryset.filter(id__in=sessions)
        return queryset.all()


class SessionTaskTrainingFilter(DefaultListFilter):
    title = "Training"
    parameter_name = "training"

    def lookups(self, request, model_admin):
        return [("all", "All"), ("training", "Training")]

    def queryset(self, request, queryset):
        if self.value() == "all":
            return queryset.all()
        elif self.value() == "training":
            sessions = (
                SessionTask.objects.filter(task__training=True)
                .exclude(session=None)
                .values_list("session")
            )
            return queryset.filter(id__in=sessions)


class SessionDatasetForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SessionDatasetForm, self).__init__(*args, **kwargs)


class SessionDatasetInline(nested_admin.NestedTabularInline):
    model = BuffaloDataset
    fields = ("session", "dataset_type", "collection", "file_name")
    extra = 0


class BuffaloSessionAdmin(VersionAdmin, nested_admin.NestedModelAdmin):
    form = SessionForm
    # change_list_template = "buffalo/change_list.html"
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
    inlines = [
        SessionDatasetInline,
        SessionWeighingInline,
        SessionFoodInline,
        SessionTaskInline,
        ChannelRecordingInline,
    ]
    ordering = ("-updated",)
    list_filter = [
        ("subject", RelatedDropdownFilter),
        ("start_time", DropdownFilter),
        SessionTaskListFilter,
        SessionTaskTrainingFilter,
    ]

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
            form.base_fields["subject"].initial = subject
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
                            "ripples": prev_channel.ripples,
                            "alive": prev_channel.alive,
                            "number_of_cells": prev_channel.number_of_cells,
                            "notes": prev_channel.notes,
                        }
                    )
                inlines = [
                    SessionDatasetInline,
                    SessionWeighingInline,
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
            if isinstance(instance, WeighingLog):
                instance.subject = form.instance.subject
            if isinstance(instance, ChannelRecording):
                if instance.electrode is not None:
                    instance.save()
                else:
                    continue
            instance.save()
        formset.save_m2m()


class BuffaloWeight(BaseAdmin):
    form = SubjectWeighingForm
    change_form_template = "buffalo/change_form.html"
    source = ""

    list_display = [
        "subject",
        "weight_in_Kg",
        "user",
        "_session",
        "date_time",
    ]
    ordering = ("-updated",)

    def _session(self, obj):
        try:
            url = reverse("session-details", kwargs={"session_id": obj.session.id})
        except AttributeError:
            url = ""

        return format_html('<a href="{url}">{name}</a>', url=url, name=obj.session.name)

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

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.session is not None:
            return False

        return True

    def has_delete_permission(self, request, obj=None):
        if obj is not None and obj.session is not None:
            return False
        return True


class BuffaloSessionTask(BaseAdmin):
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

    def has_delete_permission(self, request, obj=None):
        if "buffalosession/add/" in request.path:
            return False
        if "buffalo/task" in request.path:
            try:
                task = SessionTask.objects.filter(
                    task=request.resolver_match.kwargs["object_id"]
                ).exists()

                if task:
                    return False
            except KeyError:
                pass

        return True

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

    def clean(self):
        super().clean()
        for form in self.forms:
            form.instance.subject = form.cleaned_data["electrode"].subject


class StartingPointInline(nested_admin.NestedTabularInline):
    model = StartingPoint
    formset = StartingPointFormset
    fields = (
        "electrode",
        "x",
        "y",
        "z",
        "x_norm",
        "y_norm",
        "z_norm",
        "starting_point_set",
        "depth",
        "date_time",
        "notes",
    )
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "starting_point_set":
            try:
                subject_id = request.resolver_match.kwargs["object_id"]
                kwargs["queryset"] = StartingPointSet.objects.prefetch_related(
                    "subject"
                ).filter(subject=subject_id)
            except KeyError:
                pass
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class BuffaloElectrode(nested_admin.NestedTabularInline):
    model = Electrode
    fields = ("channel_number", "turns_per_mm", "millimeters", "date_time", "notes")
    extra = 0
    inlines = [StartingPointInline]
    ordering = ("created",)


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

        def formfield_for_foreignkey(self, db_field, request, **kwargs):
            if db_field.name == "electrode":
                try:
                    kwargs["queryset"] = Electrode.objects.prefetch_related(
                        "subject"
                    ).filter(subject=subject_id)
                except KeyError:
                    pass
            return super().formfield_for_foreignkey(db_field, request, **kwargs)

        class ElectrodeLogInlineFormSet(BaseInlineFormSet):
            def __init__(self, *args, **kwargs):
                kwargs["initial"] = data
                super(BuffaloElectrodeLog.ElectrodeLogInlineFormSet, self).__init__(
                    *args, **kwargs
                )

        model = ElectrodeLog
        extra = num_forms
        fields = ("electrode", "turn", "impedance", "date_time", "notes")
        formset = ElectrodeLogInlineFormSet

    return BuffaloElectrodeLog


class BuffaloElectrodeLogSubjectAdmin(admin.ModelAdmin):

    change_form_template = "buffalo/change_form.html"
    form = ElectrodeLogSubjectForm
    list_display = [
        "nickname",
        "birth_date",
        "sex",
        "description",
        "responsible_user",
    ]
    fields = ["nickname", "unique_id", "name", "prior_order"]
    search_fields = [
        "nickname",
    ]

    def save_formset(self, request, form, formset, change):
        if "prior_order" in form.cleaned_data and form.cleaned_data["prior_order"]:
            delta = 0
            datetime_base = datetime.now()
            for inline_form in formset.forms:
                if inline_form.has_changed():
                    if delta == 0:
                        datetime_base = inline_form.instance.date_time
                    inline_form.instance.date_time = datetime_base + timedelta(
                        seconds=delta
                    )
                    delta += 1
                    super().save_formset(request, form, formset, change)
        super().save_formset(request, form, formset, change)

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
    list_display = [
        "subject",
        "electrode",
        "turn",
        "impedance",
        "current_location",
        "date_time",
    ]
    fields = ("subject", "electrode", "turn", "impedance", "date_time", "notes")
    search_fields = [
        "subject__nickname",
    ]
    ordering = ["-date_time"]


class BuffaloChannelRecording(BaseAdmin):
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


class BuffaloSTLFile(BaseAdmin):
    change_form_template = "buffalo/change_form.html"
    fields = ("stl_file", "subject")

    def response_add(self, request, obj):
        messages.success(request, "File uploaded successful.")
        return redirect("/buffalo/buffalosubject")

    def __init__(self, *args, **kwargs):
        super(BuffaloSTLFile, self).__init__(*args, **kwargs)
        if self.fields and "json" in self.fields:
            fields = list(self.fields)
            fields.remove("json")
            self.fields = tuple(fields)

    def get_form(self, request, obj=None, **kwargs):
        form = super(BuffaloSTLFile, self).get_form(request, obj, **kwargs)
        subject_id = request.GET.get("subject", None)
        if subject_id:
            form.base_fields["subject"].initial = subject_id
        return form


class BuffaloStartingPoint(admin.ModelAdmin):
    change_form_template = "buffalo/change_form.html"


class BuffaloStartingPointSet(BaseAdmin):
    change_form_template = "buffalo/change_form.html"

    fields = ["name", "subject"]

    def __init__(self, *args, **kwargs):
        super(BuffaloStartingPointSet, self).__init__(*args, **kwargs)
        if self.fields and "json" in self.fields:
            fields = list(self.fields)
            fields.remove("json")
            self.fields = tuple(fields)


class BuffaloCategory(BaseAdmin):
    change_form_template = "buffalo/change_form.html"
    form = TaskCategoryForm


class FoodTypeAdmin(BaseAdmin):
    form = FoodTypeForm

    def has_delete_permission(self, request, obj=None):
        if "buffalo/buffalosession" in request.path:
            return False
        return True


class BuffaloDatasetAdmin(BaseExperimentalDataAdmin):
    # change_list_template = "buffalo/change_list.html"
    fields = [
        "name",
        "session",
        "dataset_type",
        "session_task",
        "collection",
        "file_size",
    ]
    readonly_fields = ["name_", "session", "_online"]
    list_display = [
        "name_",
        "_online",
        "version",
        "collection",
        "dataset_type_",
        "file_size",
        "session",
        "created_by",
        "created_datetime",
    ]

    list_filter = [
        ("created_by", RelatedDropdownFilter),
        ("created_datetime", DateRangeFilter),
        ("dataset_type", RelatedDropdownFilter),
    ]
    search_fields = (
        "created_by__username",
        "name",
        "session__subject__nickname",
        "dataset_type__name",
        "dataset_type__filename_pattern",
    )
    ordering = ("-created_datetime",)

    def get_queryset(self, request):
        qs = super(BuffaloDatasetAdmin, self).get_queryset(request)
        qs = qs.select_related(
            "dataset_type", "session", "session_task", "session__subject", "created_by"
        )
        return qs

    def dataset_type_(self, obj):
        return obj.dataset_type.name

    def name_(self, obj):
        return obj.name or "<unnamed>"

    def subject(self, obj):
        return obj.session.subject.nickname

    def _online(self, obj):
        return obj.online

    _online.short_description = "On server"
    _online.boolean = True

    def has_add_permission(self, request, obj=None):
        return False


admin.site.register(BuffaloSubject, BuffaloSubjectAdmin)
admin.site.register(BuffaloElectrodeSubject, BuffaloElectrodeSubjectAdmin)
admin.site.register(BuffaloElectrodeLogSubject, BuffaloElectrodeLogSubjectAdmin)
admin.site.register(ElectrodeLog, BuffaloElectrodeLogAdmin)
admin.site.register(BuffaloSession, BuffaloSessionAdmin)
admin.site.register(WeighingLog, BuffaloWeight)
admin.site.register(SessionTask, BuffaloSessionTask)
admin.site.register(Task, BuffaloTask)
admin.site.register(FoodLog, BuffaloSubjectFood)
admin.site.register(StartingPoint, BuffaloStartingPoint)
admin.site.register(StartingPointSet, BuffaloStartingPointSet)
admin.site.register(STLFile, BuffaloSTLFile)
admin.site.register(ChannelRecording, BuffaloChannelRecording)
admin.site.register(ProcessedRecording)
admin.site.register(TaskCategory, BuffaloCategory)
admin.site.register(Location)
admin.site.register(Reward)
admin.site.register(Platform)
admin.site.register(FoodType, FoodTypeAdmin)
admin.site.register(BuffaloDataset, BuffaloDatasetAdmin)
