from django.urls import path
from . import views

app_name = "admin"

urlpatterns = [
    path("dashboard/", views.dashboard_simplified, name="dashboard_simple"),

    # report actions
    path("report/<int:report_id>/approve/", views.approve_report, name="approve_report"),
    path("report/<int:report_id>/reject/", views.reject_report, name="reject_report"),
    path("report/<int:report_id>/delete/", views.delete_report, name="delete_report"),
    path("coach/<int:coach_id>/ban/", views.ban_coach, name="ban_coach"),

    # coach approval actions
    path("coach/<int:coach_id>/approve/", views.approve_coach, name="approve_coach"),
    path("coach/<int:coach_id>/reject/", views.reject_coach, name="reject_coach"),
]
