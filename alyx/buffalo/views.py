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
from multi_form_view import MultiFormView
from django.urls import reverse
from django.http import JsonResponse
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder

from actions.models import Session
from subjects.models import Subject
from .models import Task, SessionTask, DailyObservation
from .forms import (
    TaskForm,
    SessionForm,
    SubjectForm,
    DailyObservationForm,
    TaskSessionForm,
)


class TaskCreateView(CreateView):
    template_name = "buffalo/task.html"
    form_class = TaskForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["objects"] = Task.objects.exclude(name="")
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


class subjectCreateView(CreateView):
    template_name = "buffalo/subject.html"
    form_class = SubjectForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["objects"] = Subject.objects.all()
        context["observations"] = DailyObservation.objects.all()
        # import pdb; pdb.set_trace()
        # context["subjects"] = Subject.objects.all()
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
    template_name = "buffalo/subject.html"
    form_class = DailyObservationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["objects"] = DailyObservation.objects.all()
        # import pdb; pdb.set_trace()
        # context["subjects"] = Subject.objects.all()
        return context

    def get_success_url(self):
        return reverse("buffalo-sessions")


class SessionCreateView(CreateView):
    template_name = "buffalo/session.html"
    form_class = SessionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["objects"] = Session.objects.exclude(name="")
        context["form_task"] = TaskSessionForm()
        # import pdb; pdb.set_trace()

        # import pdb; pdb.set_trace()
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
                    "session__name",
                    "session__start_time",
                    "date_time",
                    "general_comments",
                    "task_sequence",
                    "dataset_type",
                )
                .order_by("task_sequence")
            )
            # import pdb; pdb.set_trace()
            data = json.dumps(list(tasks), cls=DjangoJSONEncoder)
            return JsonResponse({"tasks": data}, status=200)


class CreateTasksToSession(CreateView):
    template_name = "buffalo/tasks_selector_modal.html"
    form_class = TaskSessionForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sessions = Session.objects.all()
        context["objects"] = sessions.select_related("subject", "lab", "project")
        context["form_task"] = TaskSessionForm()

        # context["subjects"] = Subject.objects.all()
        return context

    def get_success_url(self):
        return reverse("buffalo-sessions")
