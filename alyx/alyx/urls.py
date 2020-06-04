from django.conf.urls import include
from django.urls import path, re_path
from django.contrib import admin
from rest_framework.authtoken import views as authv
from rest_framework.documentation import include_docs_urls

from subjects import views as sv
from actions import views as av
from data import views as dv
from misc import views as mv
from buffalo import views as bf
from buffalo.views import (
    TaskCreateView,
    SessionCreateView,
    getTaskCategoryJson,
    CreateTasksToSession,
    TaskUpdateView,
    subjectUpdateView,
    TaskCreateVersionView,
    SubjectWeighingCreateView,
    SessionDetails,
    SubjectDetailView,
    getTaskDatasetType,
)


register_file = dv.RegisterFileViewSet.as_view({"post": "create"})
sync_file_status = dv.SyncViewSet.as_view({"post": "sync", "get": "sync_status"})
new_download = dv.DownloadViewSet.as_view({"post": "create"})

user_list = mv.UserViewSet.as_view({"get": "list"})

user_detail = mv.UserViewSet.as_view({"get": "retrieve"})


#admin.site.site_header = "Alyx"
admin.site.site_header = "Buffalo"

urlpatterns = [
    #path("", mv.api_root),
    path("", admin.site.urls),
    path("", include("experiments.urls")),
    path("admin/", admin.site.urls),
    #path("admin-subjects/", include("subjects.urls")),
    #path("admin-actions/", include("actions.urls")),
    #path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    #path("auth-token", authv.obtain_auth_token),
    path("data-formats", dv.DataFormatList.as_view(), name="dataformat-list"),
    path(
        "data-formats/<str:name>",
        dv.DataFormatDetail.as_view(),
        name="dataformat-detail",
    ),
    path(
        "data-repository-type",
        dv.DataRepositoryTypeList.as_view(),
        name="datarepositorytype-list",
    ),
    path(
        "data-repository-type/<str:name>",
        dv.DataRepositoryTypeDetail.as_view(),
        name="datarepositorytype-detail",
    ),
    path(
        "data-repository", dv.DataRepositoryList.as_view(), name="datarepository-list"
    ),
    path(
        "data-repository/<str:name>",
        dv.DataRepositoryDetail.as_view(),
        name="datarepository-detail",
    ),
    path("datasets", dv.DatasetList.as_view(), name="dataset-list"),
    path("datasets/<uuid:pk>", dv.DatasetDetail.as_view(), name="dataset-detail"),
    path("dataset-types", dv.DatasetTypeList.as_view(), name="datasettype-list"),
    path(
        "dataset-types/<str:name>",
        dv.DatasetTypeDetail.as_view(),
        name="datasettype-detail",
    ),
    path("docs/", include_docs_urls(title="Alyx REST API documentation")),
    path("downloads", dv.DownloadList.as_view(), name="download-list"),
    path("downloads/<uuid:pk>", dv.DownloadDetail.as_view(), name="download-detail"),
    path("files", dv.FileRecordList.as_view(), name="filerecord-list"),
    path("files/<uuid:pk>", dv.FileRecordDetail.as_view(), name="filerecord-detail"),
    path("labs", mv.LabList.as_view(), name="lab-list"),
    path("labs/<str:name>", mv.LabDetail.as_view(), name="lab-detail"),
    path("locations", av.LabLocationList.as_view(), name="location-list"),
    path(
        "locations/<str:name>",
        av.LabLocationAPIDetails.as_view(),
        name="location-detail",
    ),
    path("new-download", new_download, name="new-download"),
    path("projects", sv.ProjectList.as_view(), name="project-list"),
    path("projects/<str:name>", sv.ProjectDetail.as_view(), name="project-detail"),
    path("register-file", register_file, name="register-file"),
    path("sessions", av.SessionAPIList.as_view(), name="session-list"),
    path("sessions/<uuid:pk>", av.SessionAPIDetail.as_view(), name="session-detail"),
    path("subjects", sv.SubjectList.as_view(), name="subject-list"),
    path("subjects/<str:nickname>", sv.SubjectDetail.as_view(), name="subject-detail"),
    path("sync-file-status", sync_file_status, name="sync-file-status"),
    re_path("^uploaded/(?P<img_url>.*)", mv.UploadedView.as_view(), name="uploaded"),
    path("users", user_list, name="user-list"),
    path("users/<str:username>", user_detail, name="user-detail"),
    path(
        "water-administrations",
        av.WaterAdministrationAPIListCreate.as_view(),
        name="water-administration-create",
    ),
    path(
        "water-administrations/<uuid:pk>",
        av.WaterAdministrationAPIDetail.as_view(),
        name="water-administration-detail",
    ),
    path(
        "water-requirement/<str:nickname>",
        av.WaterRequirement.as_view(),
        name="water-requirement",
    ),
    path(
        "water-restriction",
        av.WaterRestrictionList.as_view(),
        name="water-restriction-list",
    ),
    path(
        "water-restricted-subjects",
        sv.WaterRestrictedSubjectList.as_view(),
        name="water-restricted-subject-list",
    ),
    path("water-type", av.WaterTypeList.as_view(), name="watertype-list"),
    path("water-type/<str:name>", av.WaterTypeList.as_view(), name="watertype-detail"),
    path("weighings", av.WeighingAPIListCreate.as_view(), name="weighing-create"),
    path("weighings/<uuid:pk>", av.WeighingAPIDetail.as_view(), name="weighing-detail"),
    path("buffalo-tasks/", TaskCreateView.as_view(), name="buffalo-tasks"),
    path("buffalo-sessions/", SessionCreateView.as_view(), name="buffalo-sessions"),
    
    path(
        "buffalo-get-task-category-json/",
        getTaskCategoryJson.as_view(),
        name="buffalo-get-task-category-json",
    ),
    path("buffalo-add-task/", CreateTasksToSession.as_view(), name="buffalo-add-task"),
    path(
        "buffalo-edit-task/<uuid:pk>/",
        TaskUpdateView.as_view(),
        name="buffalo-edit-task",
    ),
    path(
        "buffalo-edit-subject/<uuid:pk>/",
        subjectUpdateView.as_view(),
        name="buffalo-edit-subject",
    ),
    path(
        "buffalo-task-version/<uuid:pk>/",
        TaskCreateVersionView.as_view(),
        name="buffalo-task-version",
    ),
    path(
        "buffalo-subject-weighing/",
        SubjectWeighingCreateView.as_view(),
        name="buffalo-subject-weighing",
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
]
