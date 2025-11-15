from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from django.contrib import messages
import jdatetime
from datetime import datetime, time
import pandas as pd
from io import BytesIO
from .models import RainRecord, Station
from .forms import RainRecordForm, LoginForm

TIME_RANGES = [
    ('00-03','00-03'),
    ('03-06','03-06'),
    ('06-09','06-09'),
    ('09-12','09-12'),
    ('12-15','12-15'),
    ('15-18','15-18'),
    ('18-21','18-21'),
    ('21-24','21-24'),
]

# --- صفحه اصلی ---
def index(request):
    return redirect('dashboard') if request.user.is_authenticated else redirect('login')

# --- ثبت نام ---
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

# --- ورود ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            remember = form.cleaned_data.get('remember_me')
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if not remember:
                    request.session.set_expiry(0)
                messages.success(request, f"{user.username} عزیز، خوش آمدید 🌦️")
                return redirect('dashboard')
            else:
                messages.error(request, "❌ نام کاربری یا رمز عبور اشتباه است.")
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

# --- خروج ---
def logout_view(request):
    logout(request)
    return redirect('login')

# --- ثبت رکورد ---
@login_required
def enter_record(request):
    if request.method == 'POST':
        form = RainRecordForm(request.POST)
        date_str = request.POST.get('date', '').strip()
        time_range = request.POST.get('time_range', '00-03')
        if form.is_valid():
            rec = form.save(commit=False)
            rec.user = request.user
            try:
                jdate = jdatetime.datetime.strptime(date_str, '%Y/%m/%d')
                gdate = jdate.togregorian().date()
                start_hour = int(time_range.split('-')[0])
                ts = datetime.combine(gdate, time(start_hour,0))
                if settings.USE_TZ:
                    ts = timezone.make_aware(ts, timezone.get_default_timezone())
                rec.timestamp = ts
                rec.time_range = time_range
                rec.save()
                messages.success(request, "✅ داده با موفقیت ثبت شد.")
                return redirect('enter')
            except Exception as e:
                messages.error(request, f"فرمت تاریخ یا ساعت نامعتبر: {e}")
        else:
            messages.error(request, "فرم نامعتبر است.")
    else:
        form = RainRecordForm()
    stations = Station.objects.all()
    return render(request, 'enter.html', {
        'form': form,
        'time_choices': TIME_RANGES,
        'stations': stations,
    })

# --- داشبورد ---
@login_required
def dashboard(request):
    station_filter = request.GET.get("station", "all")
    start_date = request.GET.get("start_date", "")
    end_date = request.GET.get("end_date", "")

    records = RainRecord.objects.select_related('station','user').order_by('-timestamp')

    if station_filter != "all":
        records = records.filter(station_id=station_filter)

    try:
        if start_date:
            j_start = jdatetime.datetime.strptime(start_date, '%Y/%m/%d')
            g_start = j_start.togregorian().replace(hour=0, minute=0, second=0)
            records = records.filter(timestamp__gte=g_start)
        if end_date:
            j_end = jdatetime.datetime.strptime(end_date, '%Y/%m/%d')
            g_end = j_end.togregorian().replace(hour=23, minute=59, second=59)
            records = records.filter(timestamp__lte=g_end)
    except:
        pass

    stations = Station.objects.all()
    return render(request, "dashboard.html", {
        "records": records,
        "stations": stations,
        "station_filter": station_filter,
        "start_date": start_date,
        "end_date": end_date,
        "time_choices": TIME_RANGES,
    })

# --- حذف رکورد ---
@login_required
def delete_record(request, record_id):
    record = get_object_or_404(RainRecord, pk=record_id)
    if request.method == 'POST':
        record.delete()
        messages.success(request, "رکورد با موفقیت حذف شد.")
        return redirect('dashboard')
    return render(request, 'records/delete_record.html', {'record': record})

# --- بروزرسانی inline ---
@login_required
@csrf_exempt
def inline_update(request):
    if request.method != 'POST':
        return JsonResponse({'status':'error','message':'درخواست باید POST باشد'}, status=400)
    record_id = request.POST.get('id')
    field = request.POST.get('field')
    value = request.POST.get('value')
    record = get_object_or_404(RainRecord, pk=record_id)
    try:
        if field == 'rainfall_mm':
            record.rainfall_mm = float(value)
        elif field == 'time_range':
            record.time_range = value
        record.save()
        return JsonResponse({'status':'success'})
    except Exception as e:
        return JsonResponse({'status':'error','message': str(e)}, status=400)

# --- خروجی Excel ---
@login_required
def export_excel(request):
    qs = RainRecord.objects.select_related('station','user').order_by('timestamp')
    data = []
    for r in qs:
        ts = r.timestamp
        if ts and ts.tzinfo:
            ts = ts.replace(tzinfo=None)
        data.append({
            'user': r.user.username,
            'station': r.station.name,
            'date': jdatetime.datetime.fromgregorian(datetime=ts).strftime('%Y/%m/%d') if ts else '',
            'time_range': r.time_range,
            'rainfall_mm': r.rainfall_mm,
        })
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='rainfall')
    output.seek(0)
    response = HttpResponse(output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=rainfall_records.xlsx'
    return response
