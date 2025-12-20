from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from .models import Report, AdminAction
from coaches_book_catalog.models import Coach, CoachRequest
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def dashboard_simple(request):
    if not request.user.is_superuser:
        if hasattr(request.user, 'is_customer') and request.user.is_customer:
            return redirect('customer_dashboard') 
        if hasattr(request.user, 'is_coach') and request.user.is_coach:
            return redirect('coach_dashboard')
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

        req.user.user_type = 'coach'
        req.user.save()

        AdminAction.objects.create(
            action_type="APPROVE",
            note=f"Approved coach request for {req.user.username}",
        )

        messages.success(request, f"Coach {req.name} approved successfully!", extra_tags='admin')
    else:
        messages.info(request, f"Coach {req.name} is already approved.")

    return redirect('my_admin:dashboard_simple')

@require_POST
def reject_coach(request, coach_id):
    req = get_object_or_404(CoachRequest, pk=coach_id)
    username = req.user.username
    req.user.user_type = 'customer'
    req.user.save()
    req.delete()

    messages.info(request, f"Coach request from {username} rejected.", extra_tags='admin')
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

    messages.warning(request, f"Coach {username} has been banned and deleted.", extra_tags='admin')
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

    messages.success(request, "Report deleted successfully.", extra_tags='admin')
    return redirect('my_admin:dashboard_simple')

@csrf_exempt
def approve_coach_api(request, coach_id):
    if request.method != 'POST':
        return JsonResponse({'status': False, 'message': 'Method tidak diizinkan'}, status=405)

    req = get_object_or_404(CoachRequest, pk=coach_id)

    if req.approved:
        return JsonResponse({'status': False, 'message': 'Coach sudah disetujui'}, status=400)

    # Create coach profile
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

    req.user.user_type = 'coach'
    req.user.save()

    AdminAction.objects.create(
        action_type="APPROVE",
        note=f"Approved coach request for {req.user.username}",
    )

    return JsonResponse({'status': True, 'message': 'Coach approved'})

@csrf_exempt
def reject_coach_api(request, coach_id):
    if request.method != 'POST':
        return JsonResponse({'status': False, 'message': 'Method tidak diizinkan'}, status=405)

    req = get_object_or_404(CoachRequest, pk=coach_id)
    username = req.user.username

    req.user.user_type = 'customer'
    req.user.save()
    req.delete()

    return JsonResponse({
        'status': True,
        'message': f'Coach request dari {username} telah ditolak'
    })


@csrf_exempt
def ban_coach_api(request, coach_id):
    if request.method != 'POST':
        return JsonResponse({'status': False, 'message': 'Method tidak diizinkan'}, status=405)

    coach = get_object_or_404(Coach, pk=coach_id)
    username = coach.user.username

    coach.user.delete()

    AdminAction.objects.create(
        action_type="BAN_COACH",
        note=f"Banned coach {username}",
    )

    return JsonResponse({
        'status': True,
        'message': f'Coach {username} telah di-ban dan akunnya dihapus'
    })

@csrf_exempt
def delete_report_api(request, report_id):
    if request.method != 'POST':
        return JsonResponse({'status': False, 'message': 'Method tidak diizinkan'}, status=405)

    report = get_object_or_404(Report, pk=report_id)
    report.delete()

    AdminAction.objects.create(
        action_type="DELETE_REPORT",
        note=f"Deleted report ID {report_id}",
    )

    return JsonResponse({'status': True, 'message': 'Report berhasil dihapus'})

@csrf_exempt
def api_reports(request):
    reports = Report.objects.filter(
        is_reviewed=False,
        is_approved=False
    )

    data = []
    for r in reports:
        data.append({
            "id": r.id,
            "reason": r.reason,
            "coach_id": r.coach.id,
            "coach_username": r.coach.user.username,
            "reporter": r.reporter.username,
            "created_at": r.created_at.isoformat(),
        })

    return JsonResponse({
        "reports": data
    })

@login_required
@require_POST
def api_create_report(request, coach_id):
    if coach_id == 0:
        return JsonResponse({
            'success': False,
            'error': 'Invalid coach_id'
        }, status=400)

    reason = request.POST.get('reason', '').strip()
    if not reason:
        return JsonResponse({
            'success': False,
            'error': 'Reason is required'
        }, status=400)

    coach = get_object_or_404(Coach, id=coach_id)

    Report.objects.create(
        reporter=request.user,
        coach=coach,
        reason=reason
    )

    return JsonResponse({
        'success': True,
        'message': 'Report submitted successfully'
    })

@login_required
def list_reports_api(request):
    if not request.user.is_superuser:
        return JsonResponse({'status': False, 'message': 'Forbidden'}, status=403)

    reports = Report.objects.select_related('coach', 'reporter')

    data = [
        {
            'id': r.id,
            'coach_id': r.coach.id,
            'coach_name': r.coach.name,
            'coach_username': r.coach.user.username,
            'reporter': r.reporter.username,
            'reason': r.reason,
            'created_at': r.created_at,
        }
        for r in reports
    ]

    return JsonResponse({
        'status': True,
        'reports': data
    })

@csrf_exempt
def api_coach_requests(request):
    pending = CoachRequest.objects.filter(approved=False).select_related("user")

    data = []
    for c in pending:
        data.append({
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "user_username": c.user.username,
            "created_at": c.created_at.isoformat(),
        })

    return JsonResponse({"requests": data}, status=200)

