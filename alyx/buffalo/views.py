import json

from rest_framework import generics
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from django.views.generic import (
    View,
    CreateView,
    TemplateView,
    FormView,
    DetailView,
    UpdateView,
)
from django.urls import reverse
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder

from actions.models import Session, Weighing
from subjects.models import Subject
from .models import Task, SessionTask, DailyObservation, SubjectFood
from .forms import (
    TaskForm,
    SessionForm,
    SubjectForm,
    DailyObservationForm,
    TaskSessionForm,
    TaskVersionForm,
    WeighingForm,
    SubjectFoodForm,
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


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm

    def get_context_data(self, **kwargs):
        context = super(TaskUpdateView, self).get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse("buffalo-tasks")


class TaskCreateVersionView(CreateView):
    template_name = "buffalo/task_form.html"
    model = Task
    form_class = TaskVersionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        if form.instance.original_task is None:
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
        return reverse("buffalo-tasks")


class subjectCreateView(CreateView):
    template_name = "buffalo/subject.html"
    form_class = SubjectForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["objects"] = Subject.objects.all()
        context["form_weight"] = WeighingForm()
        context["form_food"] = SubjectFoodForm()

        return context

    def get_success_url(self):
        return reverse("buffalo-subjects")


class subjectUpdateView(UpdateView):
    template_name = "buffalo/subject_form.html"
    model = Subject
    form_class = SubjectForm

    def get_context_data(self, **kwargs):
        context = super(subjectUpdateView, self).get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse("buffalo-subjects")


class DailyObservationCreateView(CreateView):
    template_name = "buffalo/daily_observation_form.html"
    form_class = DailyObservationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_form(self, form_class=None):
        if self.request.method == "GET":
            subject = Subject.objects.get(pk=self.kwargs["pk"])
            form = DailyObservationForm(initial=({"subject": subject.id}))
            return form
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(**self.get_form_kwargs())

    def get_success_url(self):
        return reverse("buffalo-subjects")


class SessionCreateView(CreateView):
    template_name = "buffalo/session.html"
    form_class = SessionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["objects"] = Session.objects.exclude(name="")
        context["form_task"] = TaskSessionForm()

        return context

    def get_success_url(self):
        return reverse("buffalo-sessions")


class AddTasksToSessionAjax(View):
    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            session_id = request.GET.get("session_id")
            tasks = (
                SessionTask.objects.filter(session=session_id)
                .values(
                    "task__name",
                    "task__version",
                    "session__name",
                    "session__start_time",
                    "date_time",
                    "general_comments",
                    "task_sequence",
                    "dataset_type",
                )
                .order_by("task_sequence")
            )
            data = json.dumps(list(tasks), cls=DjangoJSONEncoder)
            return JsonResponse({"tasks": data}, status=200)


class CreateTasksToSession(CreateView):
    template_name = "buffalo/tasks_selector_modal.html"
    form_class = TaskSessionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sessions = Session.objects.all()
        context["objects"] = sessions.select_related("subject", "lab", "project")

        return context

    def get_success_url(self):
        return reverse("buffalo-sessions")


class SubjectDetailView(TemplateView):
    template_name = "buffalo/subject_details.html"

    def get(self, request, *args, **kwargs):
        subject_id = self.kwargs["pk"]
        context = {
            "subject": Subject.objects.get(pk=subject_id),
            "observations": DailyObservation.objects.filter(subject=subject_id),
            "sessions": Session.objects.filter(subject=subject_id),
            "weights": Weighing.objects.filter(subject=subject_id),
            "food": SubjectFood.objects.filter(subject=subject_id),
        }

        return self.render_to_response(context)


class SubjectWeighingCreateView(CreateView):
    template_name = "buffalo/subject_weight.html"
    form_class = WeighingForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def get_success_url(self):
        return reverse("buffalo-subjects")


class SubjectFoodCreateView(CreateView):
    template_name = "buffalo/subject_food.html"
    form_class = SubjectFoodForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

    def get_success_url(self):
        return reverse("buffalo-subjects")
