import datetime

from plotly.subplots import make_subplots
import plotly.offline as opy
import plotly.graph_objs as go
import trimesh

from django.views.generic import (
    View,
    CreateView,
    TemplateView,
    FormView,
)
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.shortcuts import render
from django.conf import settings
from .utils import (
    get_mat_file_info,
    download_csv_points_mesh,
    get_electrodelog_info,
    get_channelrecording_info,
)

from actions.models import Session, Weighing
from .models import (
    Task,
    SessionTask,
    FoodLog,
    ChannelRecording,
    TaskCategory,
    BuffaloSession,
    BuffaloSubject,
    Electrode,
    ElectrodeLog,
    WeighingLog,
    StartingPointSet,
    BuffaloDataset,
)
from .forms import (
    TaskForm,
    TaskVersionForm,
    ElectrodeBulkLoadForm,
    ElectrodeLogBulkLoadForm,
    ChannelRecordingBulkLoadForm,
    PlotFilterForm,
    SessionQueriesForm,
)


class TaskCreateView(CreateView):
    template_name = "buffalo/task.html"
    form_class = TaskForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["objects"] = Task.objects.exclude(name="").order_by("name")
        return context

    def get_success_url(self):
        return reverse("buffalo-tasks")


class TaskCreateVersionView(CreateView):
    template_name = "buffalo/admin_task_form.html"
    model = Task
    form_class = TaskVersionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        form.instance.original_task = str(self.kwargs["pk"])
        form.instance.first_version = False
        form.instance.version = str(
            Task.objects.filter(original_task=self.kwargs["pk"]).count() + 2
        )
        form.save()

        return super(TaskCreateVersionView, self).form_valid(form)

    def get_form(self, form_class=None):
        if self.request.method == "GET":
            task = Task.objects.get(pk=self.kwargs["pk"])
            form = TaskVersionForm(
                initial=(
                    {
                        "name": task.name,
                        "description": task.description,
                        "training": task.training,
                        "platform": task.platform,
                        "category": task.category,
                        "json": task.json,
                        "reward": task.reward,
                        "location": task.location,
                        "dataset_type": task.dataset_type,
                        "version": task.version,
                        "original_task": task.original_task,
                    }
                )
            )
            return form
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_success_url(self):
        return reverse("admin:index")


class getTaskCategoryJson(View):
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            task_category = request.GET.get("task_category_id")
            category = TaskCategory.objects.get(pk=task_category)
            data = category.json
            return JsonResponse({"category_json": data}, status=200)


class SubjectDetailView(TemplateView):
    template_name = "buffalo/admin_subject_details.html"

    def get(self, request, *args, **kwargs):
        subject_id = self.kwargs["subject_id"]
        context = {
            "subject": BuffaloSubject.objects.get(pk=subject_id),
            "sessions": Session.objects.filter(subject=subject_id).order_by(
                "-start_time"
            ),
            "weights": Weighing.objects.filter(subject=subject_id).order_by(
                "-date_time"
            ),
            "food": FoodLog.objects.filter(subject=subject_id),
        }

        return self.render_to_response(context)


class SessionDetails(TemplateView):
    template_name = "buffalo/admin_session_details.html"

    def get(self, request, *args, **kwargs):
        session_id = self.kwargs["session_id"]
        all_session_tasks = (
            SessionTask.objects.filter(session=session_id)
            .values(
                "id",
                "task__id",
                "task__name",
                "task__version",
                "session__name",
                "session__start_time",
                "date_time",
                "needs_review",
                "general_comments",
                "task_sequence",
                "dataset_type__name",
            )
            .order_by("task_sequence")
        )
        channels_recording = []
        session_task_dataset_type = {}

        session_tasks = []
        for session_task in all_session_tasks:
            session_task_id = session_task["task__id"]
            session_task_datasets = BuffaloDataset.objects.filter(
                session_task=session_task["id"]
            ).values("file_name", "collection")
            if session_task_id in session_task_dataset_type:
                session_task_dataset_type[session_task_id].append(session_task_datasets)
            else:
                session_tasks.append(session_task)
                session_task_dataset_type.update(
                    {session_task_id: [session_task_datasets]}
                )
        channels_recording = ChannelRecording.objects.filter(
            session=session_id,
        )
        session = BuffaloSession.objects.get(pk=session_id)
        context = {
            "session": session,
            "session_users": session.users.all(),
            "session_weightlog": WeighingLog.objects.filter(session=session_id).first(),
            "session_foodlog": FoodLog.objects.filter(session=session_id).first(),
            "session_tasks": session_tasks,
            "channels_recording": list(channels_recording),
            "session_task_dataset_type": session_task_dataset_type,
            "session_datasets": BuffaloDataset.objects.filter(
                session=session_id, session_task=None
            ),
        }

        return self.render_to_response(context)


class ElectrodeBulkLoadView(FormView):
    form_class = ElectrodeBulkLoadForm
    template_name = "buffalo/electrode_bulk_load.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        subject_id = self.kwargs.pop("subject_id", None)
        if subject_id:
            kwargs["initial"] = {"subject": subject_id}
        return kwargs

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            structure_name = form.cleaned_data["structure_name"]
            subject_id = form.cleaned_data["subject"]
            subject = BuffaloSubject.objects.get(pk=subject_id)
            # Create a new Starting point set
            starting_point_set = StartingPointSet()
            starting_point_set.name = "Bulk load - %s" % (datetime.datetime.now())
            starting_point_set.subject = subject
            starting_point_set.save()

            if not structure_name:
                structure_name = subject.nickname
            electrodes_info = get_mat_file_info(
                form.cleaned_data["file"], structure_name
            )
            for electrode_info in electrodes_info:
                electrode = Electrode.objects.filter(
                    subject=subject_id, channel_number=str(electrode_info["channel"])
                ).first()
                if electrode:
                    electrode.create_new_starting_point_from_mat(
                        electrode_info, subject, starting_point_set
                    )
                else:
                    new_electrode = Electrode()
                    new_electrode.subject = subject
                    new_electrode.channel_number = str(electrode_info["channel"])
                    new_electrode.save()
                    new_electrode.create_new_starting_point_from_mat(
                        electrode_info, subject, starting_point_set
                    )
            messages.success(request, "File loaded successful.")
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse("admin:buffalo_buffalosubject_changelist")


class ElectrodeLogBulkLoadView(FormView):
    form_class = ElectrodeLogBulkLoadForm
    template_name = "buffalo/electrodelog_bulk_load.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        subject_id = self.kwargs.pop("subject_id", None)
        if subject_id:
            kwargs["initial"] = {"subject": subject_id}
        return kwargs

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            subject_id = form.cleaned_data["subject"]
            subject = BuffaloSubject.objects.get(pk=subject_id)
            electrodelogs_info = get_electrodelog_info(form.cleaned_data.get("file"))
            for electrode_info in electrodelogs_info:
                electrode = Electrode.objects.get_or_create(
                    subject=subject, channel_number=electrode_info["electrode"]
                )[0]
                for log in electrode_info["logs"]:
                    new_el = ElectrodeLog()
                    new_el.subject = subject
                    new_el.date_time = log["datetime"]
                    new_el.electrode = electrode
                    new_el.turn = log["turns"]
                    if log["impedance"] is not None:
                        new_el.impedance = log["impedance"]
                    if log["notes"] is not None:
                        new_el.notes = log["notes"]
                    new_el.save()
            messages.success(request, "File loaded successful.")
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        kwargs = super().get_form_kwargs()
        return "/buffalo/electrodelog/?subject__id__exact=" + str(kwargs["data"]["subject"])


class ChannelRecordingBulkLoadView(FormView):
    form_class = ChannelRecordingBulkLoadForm
    template_name = "buffalo/channelrecording_bulk_load.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        subject_id = self.kwargs.pop("subject_id", None)
        if subject_id:
            kwargs["initial"] = {"subject": subject_id}
        return kwargs

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            subject_id = form.cleaned_data["subject"]
            subject = BuffaloSubject.objects.get(pk=subject_id)
            channel_recording_info = get_channelrecording_info(form.cleaned_data.get("file"))
            for key, session_data in channel_recording_info.items():
                datetime_str = str(session_data["date"])
                session_name = f"{datetime_str}_{subject.nicknamesafe()}"
                session = BuffaloSession.objects.get_or_create(
                    subject=subject, name=session_name
                )[0]
                electrodes_loaded = {}
                for key, record_data in session_data["records"].items():
                    print("{} - {}".format(datetime_str, key))
                    if key in electrodes_loaded.keys():
                        electrode = electrodes_loaded[key]
                    else:
                        electrode = Electrode.objects.get_or_create(
                            subject=subject, channel_number=key
                        )[0]
                        electrodes_loaded[key] = electrode
                    new_cr = ChannelRecording()
                    new_cr.electrode = electrode
                    new_cr.session = session
                    if "value" in record_data.keys():
                        new_cr.number_of_cells = record_data["value"]
                    if "ripples" in record_data.keys():
                        new_cr.ripples = 'yes' if record_data["ripples"] == 'Y' else ''
                    new_cr.save()

            messages.success(request, "File loaded successful.")
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        kwargs = super().get_form_kwargs()
        return "/buffalo/buffalosubject/"


class PlotsView(View):
    form_class = PlotFilterForm
    template_name = "buffalo/plots.html"

    def get(self, request, *args, **kwargs):
        subject_id = self.kwargs["subject_id"]
        form = self.form_class(subject_id=subject_id)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        subject_id = self.kwargs["subject_id"]
        form = self.form_class(request.POST, subject_id=subject_id)
        if form.is_valid():
            subject = BuffaloSubject.objects.get(pk=subject_id)
            electrodes = Electrode.objects.prefetch_related("subject").filter(
                subject=subject_id
            )
            electrode_logs = (
                ElectrodeLog.objects.prefetch_related("electrode")
                .filter(subject=subject_id)
                .exclude(turn=None)
                .filter(
                    date_time__year=form.cleaned_data["date"].year,
                    date_time__month=form.cleaned_data["date"].month,
                    date_time__day=form.cleaned_data["date"].day,
                )
            )
            slt_file_name = form.cleaned_data["stl"].stl_file.name

            if form.cleaned_data["download_points"]:
                return download_csv_points_mesh(
                    subject.nickname,
                    form.cleaned_data["date"],
                    electrodes,
                    electrode_logs,
                    slt_file_name,
                )

            mesh = trimesh.load(settings.UPLOADED_PATH + slt_file_name)

            x_stl, y_stl, z_stl = mesh.vertices.T
            i, j, k = mesh.faces.T

            # Electrodes starting points data
            x = []
            y = []
            z = []
            ht = []
            for electrode in electrodes:
                sp = electrode.starting_point.latest("updated")
                x.append(sp.x)
                y.append(sp.y)
                z.append(sp.z)
                ht.append(electrode.channel_number)
            # Electrode logs data
            x_el = []
            y_el = []
            z_el = []
            ht_el = []
            for electrode_log in electrode_logs:
                location = electrode_log.get_current_location()
                x_el.append(location["x"])
                y_el.append(location["y"])
                z_el.append(location["z"])
                ht_el.append(electrode_log.electrode.channel_number)

            fig = make_subplots()
            electrodes_trace = go.Scatter3d(
                x=tuple(x),
                y=tuple(y),
                z=tuple(z),
                mode="markers",
                marker=dict(size=4),
                hovertext=ht,
                name="Starting points",
            )
            electrode_logs_trace = go.Scatter3d(
                x=tuple(x_el),
                y=tuple(y_el),
                z=tuple(z_el),
                mode="markers",
                marker=dict(color="darkred", size=4),
                hovertext=ht_el,
                name="Electrode log position",
            )
            stl_trace = go.Mesh3d(
                x=x_stl,
                y=y_stl,
                z=z_stl,
                i=i,
                j=j,
                k=k,
                showscale=True,
                opacity=0.4,
                hoverinfo="skip",
            )
            fig.add_trace(stl_trace)
            fig.add_trace(electrode_logs_trace)
            fig.add_trace(electrodes_trace)
            fig.update_layout(autosize=True, height=900)

            graph = opy.plot(fig, auto_open=False, output_type="div")

            return render(request, self.template_name, {"form": form, "graph": graph})

        return render(request, self.template_name, {"form": form})


class SessionQueriesView(View):
    form_class = SessionQueriesForm
    template_name = "buffalo/admin_session_queries.html"

    def get(self, request, *args, **kwargs):
        subject_id = self.kwargs["subject_id"]
        form = self.form_class(subject_id=subject_id)
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        subject_id = self.kwargs["subject_id"]
        form = self.form_class(request.POST, subject_id=subject_id)
        if form.is_valid():
            slt_file_name = form.cleaned_data["stl"].stl_file.name
            sessions = SessionTask.objects.filter(
                session__subject=subject_id, task=form.cleaned_data["task"]
            )
            channel_recordings = ChannelRecording.objects.filter(
                session__in=sessions.values("session"), alive="yes", ripples="yes"
            )
            queried_sessions = set()
            electrodes = {}
            if form.cleaned_data["is_in_stl"]:
                for record in channel_recordings:
                    electrode_logs = ElectrodeLog.objects.filter(
                        electrode=record.electrode,
                        date_time__year=record.session.start_time.year,
                        date_time__month=record.session.start_time.month,
                        date_time__day=record.session.start_time.day,
                    )
                    for electrode_log in electrode_logs:
                        if electrode_log.is_in_stl(slt_file_name):
                            queried_sessions.add(record.session)
                            if record.session.id not in electrodes:
                                electrodes[record.session.id] = set()
                            electrodes[record.session.id].add(electrode_log.electrode)
            else:
                for record in channel_recordings:
                    queried_sessions.add(record.session)
            final_sessions = []
            for session in list(queried_sessions):
                datasets = BuffaloDataset.objects.filter(session=session)
                session_electrodes = []
                if session.id in electrodes:
                    session_electrodes = list(electrodes[session.id])
                session_dict = {
                    "session": session,
                    "datasets": datasets,
                    "electrodes": session_electrodes,
                }
                final_sessions.append(session_dict)

            # import pdb; pdb.set_trace()
        return render(
            request, self.template_name, {"form": form, "sessions": final_sessions}
        )
