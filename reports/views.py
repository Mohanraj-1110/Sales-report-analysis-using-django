from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from reports.models import GeneratedReport
from reports.services import generate_report_file

@login_required
def report_list(request):
    reports = GeneratedReport.objects.all().order_by('-created_at')
    context = {
        'reports': reports,
    }
    return render(request, 'reports/report_list.html', context)

@login_required
def generate_report(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'sales')
        file_format = request.POST.get('format', 'csv')

        try:
            report_obj = generate_report_file(report_type, file_format, user=request.user)
            messages.success(request, f"Generated '{report_obj.name}' successfully! ({report_obj.row_count} rows)")
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")

        return redirect('reports:report_list')

    return redirect('reports:report_list')
