from django.urls import path

from buffalo.views import (
    TaskCreateView,
    getTaskCategoryJson,
    TaskCreateVersionView,
    SessionDetails,
    SubjectDetailView,
    getTaskDatasetType,
    ElectrodeBulkLoadView
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
        "buffalo-get-task-dataset-type/",
        getTaskDatasetType.as_view(),
        name="buffalo-get-task-dataset-type",
    ),
    path(
        "electrode-bulk-load/<uuid:subject_id>",
        ElectrodeBulkLoadView.as_view(),
        name="electrode-bulk-load",
    ),
]
