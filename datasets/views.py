import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datasets.models import DatasetUpload
from datasets.services import analyze_dataset_file, process_and_import_dataset

@login_required
def dataset_list(request):
    datasets = DatasetUpload.objects.all().order_by('-uploaded_at')
    context = {
        'datasets': datasets,
    }
    return render(request, 'datasets/dataset_list.html', context)

@login_required
def upload_dataset(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        name = request.POST.get('name', uploaded_file.name)
        
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in ['.csv', '.xlsx', '.xls']:
            messages.error(request, "Unsupported file format. Please upload a CSV or Excel file.")
            return redirect('datasets:upload')

        # Create record
        rec = DatasetUpload.objects.create(
            name=name,
            file=uploaded_file,
            file_type='CSV' if ext == '.csv' else 'EXCEL',
            file_size=uploaded_file.size,
            uploaded_by=request.user,
            status='Uploaded'
        )

        try:
            analysis = analyze_dataset_file(rec.file.path)
            rec.total_rows = analysis['total_rows']
            rec.detected_columns = analysis['columns']
            rec.column_mapping = analysis['detected_mapping']
            rec.validation_summary = analysis['missing_summary']
            rec.status = 'Validated'
            rec.save()
            messages.success(request, f"File '{rec.name}' uploaded and schema analyzed successfully!")
            return redirect('datasets:dataset_detail', pk=rec.id)
        except Exception as e:
            rec.status = 'Failed'
            rec.error_message = str(e)
            rec.save()
            messages.error(request, f"Validation error: {str(e)}")
            return redirect('datasets:dataset_detail', pk=rec.id)

    return render(request, 'datasets/upload.html')

@login_required
def dataset_detail(request, pk):
    dataset = get_object_or_404(DatasetUpload, pk=pk)
    context = {
        'dataset': dataset,
    }
    return render(request, 'datasets/dataset_detail.html', context)

@login_required
def trigger_import(request, pk):
    dataset = get_object_or_404(DatasetUpload, pk=pk)
    if request.method == 'POST':
        limit = int(request.POST.get('limit', 2000))
        try:
            process_and_import_dataset(dataset, max_rows=limit, user=request.user)
            messages.success(request, f"Successfully processed and ingested {dataset.valid_rows} orders from '{dataset.name}'.")
        except Exception as e:
            messages.error(request, f"Import error: {str(e)}")

    return redirect('datasets:dataset_detail', pk=dataset.id)
