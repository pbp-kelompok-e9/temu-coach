from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Report, AdminAction
from coaches_book_catalog.models import Coach

def admin_only(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            messages.error(request, "Not authorized.")
            return redirect('/')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@admin_only
def dashboard_simplified(request):
    # Report yang belum direview atau sudah (semuanya, terbaru dulu)
    reports = Report.objects.select_related('reporter', 'coach__user').order_by('-created_at')
    # Coach yang menunggu persetujuan
    pending_coaches = Coach.objects.select_related('user').filter(is_approved=False).order_by('user__username')
    return render(request, "admin/dashboard_simple.html", {
        "reports": reports,
        "pending_coaches": pending_coaches,
    })

# ====== Aksi untuk blok Report List ======
@login_required
@require_POST
@admin_only
def approve_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id, is_reviewed=False)
    report.is_reviewed, report.is_approved = True, True
    report.save()
    AdminAction.objects.create(admin=request.user, report=report, action_type="APPROVE")
    messages.success(request, "Report approved.")
    return redirect("admin:dashboard_simple")

@login_required
@require_POST
@admin_only
def reject_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id, is_reviewed=False)
    report.is_reviewed, report.is_approved = True, False
    report.save()
    AdminAction.objects.create(admin=request.user, report=report, action_type="REJECT")
    messages.info(request, "Report rejected.")
    return redirect("admin:dashboard_simple")

@login_required
@require_POST
@admin_only
def delete_report(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    AdminAction.objects.create(admin=request.user, report=report, action_type="DEL_REPORT")
    report.delete()
    messages.success(request, "Report deleted.")
    return redirect("admin:dashboard_simple")

@login_required
@require_POST
@admin_only
def ban_coach(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id)
    username = coach.user.username
    coach.user.delete()
    AdminAction.objects.create(admin=request.user, report=None, action_type="BAN", note=f"Ban {username}")
    messages.success(request, f"Coach '{username}' banned (account deleted).")
    return redirect("admin:dashboard_simple")


@login_required
@require_POST
@admin_only
def approve_coach(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id, is_approved=False)
    coach.is_approved = True
    coach.save()
    AdminAction.objects.create(admin=request.user, report=None, action_type="APPROVE_COACH", note=coach.user.username)
    messages.success(request, f"Coach {coach.user.username} approved.")
    return redirect("admin:dashboard_simple")

@login_required
@require_POST
@admin_only
def reject_coach(request, coach_id):
    coach = get_object_or_404(Coach, pk=coach_id, is_approved=False)
    username = coach.user.username
    coach.user.delete()
    AdminAction.objects.create(admin=request.user, report=None, action_type="REJECT_COACH", note=username)
    messages.info(request, f"Coach {username} rejected and removed.")
    return redirect("admin:dashboard_simple")
