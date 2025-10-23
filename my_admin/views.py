from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Report, AdminAction
from coaches_book_catalog.models import Coach, CoachRequest

def dashboard_simple(request):
    reports = Report.objects.select_related('reporter', 'coach__user').order_by('-created_at')
    pending_requests = CoachRequest.objects.filter(approved=False).select_related('user').order_by('-created_at')

    context = {
        'reports': reports,
        'pending_requests': pending_requests,
    }
    return render(request, 'dashboard_simple.html', context)

@require_POST
def approve_coach(request, coach_id):
    req = get_object_or_404(CoachRequest, pk=coach_id)

    if not req.approved:
        Coach.objects.create(
            user=req.user,
            name=req.name,
            age=req.age,
            citizenship=req.citizenship,
            foto=req.foto,
            club=req.club,
            license=req.license,
            preffered_formation=req.preffered_formation,
            average_term_as_coach=req.average_term_as_coach,
            description=req.description,
            rate_per_session=req.rate_per_session,
        )
        req.approved = True
        req.save()

        AdminAction.objects.create(
            action_type="APPROVE",
            note=f"Approved coach request for {req.user.username}",
        )

        messages.success(request, f"Coach {req.name} approved successfully!")
    else:
        messages.info(request, f"Coach {req.name} is already approved.")

    return redirect('my_admin:dashboard_simple')

@require_POST
def reject_coach(request, coach_id):
    req = get_object_or_404(CoachRequest, pk=coach_id)
    username = req.user.username
    req.delete()

    messages.info(request, f"Coach request from {username} rejected.")
    return redirect('my_admin:dashboard_simple')

@require_POST
def ban_coach(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id)
    username = coach.user.username
    coach.user.delete()

    AdminAction.objects.create(
        admin=request.user,
        action_type="BAN_COACH",
        note=f"Banned coach {username}",
    )

    messages.warning(request, f"Coach {username} has been banned and deleted.")
    return redirect('my_admin:dashboard_simple')

@require_POST
def delete_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    report.delete()

    AdminAction.objects.create(
        admin=request.user,
        action_type="DELETE_REPORT",
        note=f"Deleted report ID {report_id}",
    )

    messages.success(request, "Report deleted successfully.")
    return redirect('my_admin:dashboard_simple')
