from django.urls import path

from buffalo.views import (
    TaskCreateView,
    getTaskCategoryJson,
    TaskCreateVersionView,
    SessionDetails,
    SubjectDetailView,
    ElectrodeBulkLoadView,
    PlotsView,
    SessionQueriesView,
)

urlpatterns = [
    path("buffalo-tasks/", TaskCreateView.as_view(), name="buffalo-tasks"),
    path(
        "buffalo-get-task-category-json/",
        getTaskCategoryJson.as_view(),
        name="buffalo-get-task-category-json",
    ),
    path(
        "buffalo-task-version/<uuid:pk>/",
        TaskCreateVersionView.as_view(),
        name="buffalo-task-version",
    ),
    path(
        "daily-observation/<uuid:subject_id>",
        SubjectDetailView.as_view(),
        name="daily-observation",
    ),
    path(
        "session-details/<uuid:session_id>",
        SessionDetails.as_view(),
        name="session-details",
    ),
    path(
        "electrode-bulk-load/<uuid:subject_id>",
        ElectrodeBulkLoadView.as_view(),
        name="electrode-bulk-load",
    ),
    path(
        "plots/<uuid:subject_id>",
        PlotsView.as_view(),
        name="plots",
    ),
    path(
        "session-queries/<uuid:subject_id>",
        SessionQueriesView.as_view(),
        name="session-queries",
    ),
]
