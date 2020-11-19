import datetime

from plotly.subplots import make_subplots
import plotly.offline as opy
import plotly.graph_objs as go
import trimesh
import json

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
from django.db import transaction, DatabaseError

from .utils import (
    get_mat_file_info,
    download_csv_points_mesh,
    get_sessions_from_file,
    get_user_from_initial,
    get_electrodelog_info,
    get_channelrecording_info,
)
from .constants import TASK_CELLS, SESSIONS_FILE_COLUMNS
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
    FoodType,
    MenstruationLog,
    Device,
    Platform,
)
from .forms import (
    TaskForm,
    TaskVersionForm,
    ElectrodeBulkLoadForm,
    ElectrodeLogBulkLoadForm,
    ChannelRecordingBulkLoadForm,
    PlotFilterForm,
    SessionQueriesForm,
    SessionsLoadForm,
)

from .utils import (
    DEAD_VALUES,
    NUMBER_OF_CELLS_VALUES,
    ALIVE_VALUES,
    MAYBE_VALUES,
    NOT_SAVE_VALUES,
    NOT_SAVE_TASKS,
)

from .tasks import sync_electrodelogs_device


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
                "start_time",
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
                session_task_dataset_type[session_task['task_sequence']].append(
                    session_task_datasets
                )
            else:
                session_tasks.append(session_task)
                session_task_dataset_type.update(
                    {session_task['task_sequence']: [session_task_datasets]}
                )
        channels_recording = ChannelRecording.objects.filter(session=session_id,)
        session = BuffaloSession.objects.get(pk=session_id)
        context = {
            "session": session,
            "session_users": session.users.all(),
            "session_weightlog": WeighingLog.objects.filter(session=session_id).first(),
            "session_foodlog": FoodLog.objects.filter(session=session_id).first(),
            "session_menstruationlog": MenstruationLog.objects.filter(
                session=session_id
            ).first(),
            "session_tasks": all_session_tasks,
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
        device_id = self.kwargs.pop("device_id", None)
        if device_id:
            kwargs["initial"] = {"device": device_id}
        return kwargs

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            structure_name = form.cleaned_data["structure_name"]
            device_id = form.cleaned_data["device"]
            device = Device.objects.get(pk=device_id)
            subject = device.subject
            # Create a new Starting point set
            starting_point_set = StartingPointSet()
            starting_point_set.name = "Bulk load - %s" % (datetime.datetime.now())
            starting_point_set.subject = device.subject
            starting_point_set.save()

            if not structure_name:
                structure_name = subject.nickname
            electrodes_info = get_mat_file_info(
                form.cleaned_data["file"], structure_name
            )
            for electrode_info in electrodes_info:
                electrode = Electrode.objects.filter(
                    device=device_id, channel_number=str(electrode_info["channel"])
                ).first()
                if electrode:
                    electrode.create_new_starting_point_from_mat(
                        electrode_info, subject, starting_point_set
                    )
                else:
                    new_electrode = Electrode()
                    new_electrode.subject = subject
                    new_electrode.device = device
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
        kwargs = super().get_form_kwargs()
        device = Device.objects.get(pk=kwargs["data"]["device"])
        return reverse(
            "admin:buffalo_buffalodevicesubject_change", args=[device.subject.id]
        )


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
            device = form.cleaned_data["device"]
            electrodelogs_info = get_electrodelog_info(form.cleaned_data.get("file"))
            subject_electrodes = list(
                Electrode.objects.filter(subject=subject, device=device).order_by(
                    "channel_number"
                )
            )
            for electrode_info in electrodelogs_info:
                electrode = None
                for elec in subject_electrodes:
                    if elec.channel_number == str(electrode_info["electrode"]):
                        electrode = elec
                        break
                if electrode is None:
                    electrode = Electrode.objects.create(
                        device=device,
                        subject=subject,
                        channel_number=electrode_info["electrode"],
                    )
                    subject_electrodes.append(electrode)
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
                    new_el.save(sync=False)
                    if log["user"]:
                        new_el.users.set(log["user"])
                        new_el.save(sync=False)
            if not settings.TESTING:
                sync_electrodelogs_device.send(str(device.id))
            messages.success(request, "File loaded successful.")
            messages.info(request, "The platform is syncing the stl/electrodelogs info.")
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        kwargs = super().get_form_kwargs()
        return "/buffalo/electrodelog/?subject__id__exact=" + str(
            kwargs["data"]["subject"]
        )


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
            sessions = list(BuffaloSession.objects.filter(subject=subject))
            device = form.cleaned_data["device"]
            sufix = form.cleaned_data["sufix"]
            if sufix.strip() == "":
                sufix = None
            channel_recording_info = get_channelrecording_info(
                form.cleaned_data.get("file"), sufix
            )
            try:
                with transaction.atomic():
                    for key, session_data in channel_recording_info.items():
                        datetime_str = str(session_data["date"])
                        session_name = f"{datetime_str}_{subject.nicknamesafe()}"
                        session = None
                        for se in sessions:
                            if se.name == session_name:
                                session = se
                                sessions.remove(se)
                                break
                        if session is None:
                            session = BuffaloSession.objects.create(
                                subject=subject, name=session_name
                            )
                        sharp_waves = []
                        spikes = []
                        electrodes = list(Electrode.objects.filter(device__subject=subject))
                        for key, record_data in session_data["records"].items():
                            save = True
                            electrode = None
                            for el in electrodes:
                                if el.channel_number == key:
                                    electrode = el
                                    break
                            if electrode is None:
                                electrode = Electrode.objects.create(
                                    subject=subject, device=device, channel_number=key
                                )
                            new_cr = ChannelRecording.objects.create(
                                electrode=electrode, session=session
                            )
                            if "value" in record_data.keys():
                                if record_data["value"] in NUMBER_OF_CELLS_VALUES:
                                    new_cr.number_of_cells = record_data["value"]
                                    new_cr.alive = "yes"
                                elif record_data["value"] in ALIVE_VALUES:
                                    new_cr.number_of_cells = 0
                                    new_cr.alive = "yes"
                                elif record_data["value"] in MAYBE_VALUES:
                                    new_cr.alive = "maybe"
                                elif record_data["value"] in DEAD_VALUES:
                                    new_cr.alive = "no"
                                elif record_data["value"] in NOT_SAVE_VALUES:
                                    save = False
                            if "ripples" in record_data.keys():
                                new_cr.ripples = "yes" if record_data["ripples"] is True else ""
                            if (
                                "sharp_waves" in record_data.keys() and
                                record_data["sharp_waves"] is True
                            ):
                                sharp_waves.append(key)
                            if "spikes" in record_data.keys() and record_data["spikes"] is True:
                                spikes.append(key)
                            if save:
                                new_cr.save()
                            else:
                                new_cr.delete()
                        result_json = {
                            "sharp_waves": sharp_waves,
                            "spikes": spikes,
                        }
                        if session.json is not None:
                            try:
                                session_json = json.loads(session.json)
                                session_json["sharp_waves"] = result_json["sharp_waves"]
                                session_json["spikes"] = result_json["spikes"]
                                result_json = session_json
                            except:
                                print("Error reading existing session json")
                        session.json = json.dumps(result_json, indent=4)

                        if "good behavior" in session_data.keys():
                            session.needs_review = False
                        else:
                            session.needs_review = True
                        session.save(block_table=False)
            except DatabaseError:
                messages.error(
                    request,
                    "There has been an error in the database saving the Sessions",
                )
            messages.success(request, "File loaded successful.")
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        # kwargs = super().get_form_kwargs()
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
            device_id = form.cleaned_data["device"].id
            electrodes = Electrode.objects.prefetch_related("subject").filter(
                device=device_id
            )
            electrode_logs = (
                ElectrodeLog.objects.prefetch_related("electrode")
                .filter(electrode__device=device_id)
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
        return render(
            request, self.template_name, {"form": form, "sessions": final_sessions}
        )


class SessionsLoadView(FormView):
    form_class = SessionsLoadForm
    template_name = "buffalo/sessions_load.html"
    success_url = "/buffalo/buffalosession"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        subject_id = self.kwargs.pop("subject_id", None)
        if subject_id:
            kwargs["initial"] = {"subject": subject_id}
        return kwargs

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            subject_id = form.cleaned_data["subject"]
            subject = BuffaloSubject.objects.get(pk=subject_id)
            sessions = get_sessions_from_file(form.cleaned_data.get("file"))
            subject_sessions = BuffaloSession.objects.filter(subject=subject)
            tasks = list(Task.objects.all())
            platforms = list(Platform.objects.all())
            try:
                with transaction.atomic():
                    for session in sessions:
                        food_index = "3_Food (mL)"
                        session_food = (
                            0 if not session[food_index] else session[food_index]
                        )
                        food, _ = FoodType.objects.get_or_create(name="chow", unit="ml")
                        newsession_name = f"{session['0_Date (mm/dd/yyyy)']}_{subject}"
                        newsession_chamber_cleaning = session[
                            "51_Chamber Cleaning"
                        ].strip()
                        newsession = None
                        for subject_session in subject_sessions:
                            if subject_session.name == newsession_name:
                                newsession = subject_session
                                break
                        if newsession is None:
                            newsession = BuffaloSession.objects.create(
                                subject=subject,
                                name=newsession_name,
                                narrative=session["6_General Comments"],
                                pump_setting=None
                                if not session["4_Pump Setting"]
                                else session["4_Pump Setting"],
                                chamber_cleaning=None
                                if not newsession_chamber_cleaning
                                else newsession_chamber_cleaning.lower(),
                                start_time=session["0_Date (mm/dd/yyyy)"],
                            )
                        if session["1_Handler Initials"].strip():
                            session_user_obj = get_user_from_initial(
                                session["1_Handler Initials"].strip()
                            )
                            if session_user_obj:
                                newsession.users.set(session_user_obj)
                            else:
                                newsession.unknown_user = session["1_Handler Initials"]
                                newsession.save(block_table=False)
                        # If the session has weight creates the weight log
                        weight_index = "2_Weight (kg)"
                        if session[weight_index]:
                            WeighingLog.objects.create(
                                session=newsession,
                                subject=subject,
                                weight=session[weight_index],
                                date_time=session["0_Date (mm/dd/yyyy)"],
                            )
                        # Creates the food log
                        FoodLog.objects.create(
                            subject=subject,
                            food=food,
                            amount=session_food,
                            session=newsession,
                            date_time=session["0_Date (mm/dd/yyyy)"],
                        )
                        # Creates the Menstruation log
                        if session["5_Menstration"].strip() == "yes":
                            subject_mentruation_logs = MenstruationLog.objects.filter(
                                subject=subject,
                                session=newsession
                            )
                            if not subject_mentruation_logs:
                                MenstruationLog.objects.create(
                                    subject=subject, menstruation=True, session=newsession,
                                )
                        session_tasks = []
                        task_secuence = 1
                        for task_cell in TASK_CELLS:
                            cell = int(task_cell)
                            task_name_index = f"{cell}_{SESSIONS_FILE_COLUMNS[cell]}"
                            comments_index = f"{cell+2}_{SESSIONS_FILE_COLUMNS[cell+2]}"
                            start_time_index = (
                                f"{cell+1}_{SESSIONS_FILE_COLUMNS[cell+1]}"
                            )
                            task = None
                            if session[task_name_index]:
                                if session[task_name_index].lower().strip() in NOT_SAVE_TASKS:
                                    continue
                                task_info = {}
                                for t in tasks:
                                    if t.name == session[task_name_index]:
                                        task = t
                                        break
                                if task is None:
                                    task = Task.objects.create(
                                        name=session[task_name_index]
                                    )
                                if task.name.strip().endswith(".sav"):
                                    platform = None
                                    for p in platforms:
                                        if p.name == "cortex":
                                            platform = p
                                    if platform is None:
                                        platform = Platform.objects.create(
                                            name="cortex"
                                        )
                                        platforms.append(platform)
                                    if not task.platform:
                                        task.platform = platform
                                        task.save()
                                tasks.append(task)
                                task_info = {
                                    "task": task,
                                    "general_comments": session[comments_index],
                                    "session": newsession,
                                    "task_sequence": task_secuence,
                                    "start_time": None
                                    if not session[start_time_index]
                                    else session[start_time_index],
                                }
                                task_filename = (
                                    f"{cell+3}_{SESSIONS_FILE_COLUMNS[cell+3]}"
                                )
                                task_info["filename"] = (
                                    session[task_filename] if task_filename else ""
                                )
                                task_secuence += 1
                                session_tasks.append(task_info)
                        if session_tasks:
                            existing_session_tasks = list(
                                SessionTask.objects.filter(
                                    session=newsession
                                )
                            )
                            for task in session_tasks:
                                session_task = None
                                for exist_session_task in existing_session_tasks:
                                    if (
                                        task["task"] == exist_session_task.task and
                                        task["task_sequence"] == exist_session_task.task_sequence
                                    ):
                                        session_task = exist_session_task
                                        break
                                if session_task is None:
                                    session_task = SessionTask.objects.create(
                                        task=task["task"],
                                        general_comments=task["general_comments"],
                                        session=task["session"],
                                        task_sequence=task["task_sequence"],
                                        start_time=task["start_time"],
                                    )
                                existing_session_tasks.append(session_task)
                                if task["filename"]:
                                    BuffaloDataset.objects.get_or_create(
                                        file_name=task["filename"],
                                        session_task=session_task,
                                    )
            except DatabaseError:
                messages.error(
                    request,
                    "There has been an error in the database saving the Sessions",
                )
            messages.success(request, "File loaded successful.")
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        kwargs = super().get_form_kwargs()
        subject_id = kwargs["data"]["subject"]
        sessions_subject_url = f"{self.success_url}/?subject__id__exact={subject_id}"
        return sessions_subject_url
