
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import pandas as pd
from .models import RainRecord, Station
from .forms import RainRecordForm


def index(request):
    return HttpResponse("✅ سامانه ثبت بارندگی با موفقیت راه‌اندازی شد.")

def index(request):
    if request.user.is_authenticated:
        return redirect('enter')
    return render(request, 'index.html')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('enter')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('enter')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@login_required
def enter_record(request):
    if request.method == 'POST':
        form = RainRecordForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.user = request.user
            rec.save()
            return render(request, 'enter.html', {'form': RainRecordForm(), 'success': True})
    else:
        form = RainRecordForm()
    return render(request, 'enter.html', {'form': form})

@login_required
def export_excel(request):
    # Export all records to an Excel file (all users' data)
    qs = RainRecord.objects.select_related('station', 'user').all().order_by('timestamp')
    data = []
    for r in qs:
        data.append({
            'user': r.user.username,
            'station': r.station.name,
            'timestamp': r.timestamp,
            'rainfall_mm': r.rainfall_mm,
        })
    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=['user','station','timestamp','rainfall_mm'])

    # create excel in-memory
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='rainfall')
    output.seek(0)
    resp = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp['Content-Disposition'] = 'attachment; filename=all_rain_records.xlsx'
    return resp
