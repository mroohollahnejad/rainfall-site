from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
import pandas as pd
from io import BytesIO
from .models import RainRecord, Station
from .forms import RainRecordForm
from django.db.models import Q
import jdatetime
from datetime import datetime
from django.contrib import messages
from .forms import LoginForm


from django.shortcuts import redirect, render

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')  # به جای render ساده، مستقیماً به login هدایت شود

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
    """ فرم ثبت داده بارندگی """
    if request.method == 'POST':
        form = RainRecordForm(request.POST)
        if form.is_valid():
            rec = form.save(commit=False)
            rec.user = request.user
            rec.save()
            return render(request, 'enter.html', {
                'form': RainRecordForm(),
                'success': '✅ داده با موفقیت ثبت شد.'
            })
        else:
            # نمایش خطاهای اعتبارسنجی
            return render(request, 'enter.html', {
                'form': form,
                'errors': form.errors
            })
    else:
        form = RainRecordForm()
    return render(request, 'enter.html', {'form': form})


@login_required
def export_excel(request):
    """ خروجی گرفتن از داده‌های ثبت شده در قالب Excel با ستون‌های جداگانه """
    qs = RainRecord.objects.select_related('station', 'user').all().order_by('timestamp')
    data = []

    for r in qs:
        ts = r.timestamp
        if ts is not None and ts.tzinfo is not None:
            ts = ts.replace(tzinfo=None)

        year = ts.year if ts else ''
        month = ts.month if ts else ''
        day = ts.day if ts else ''
        hour = ts.hour if ts else ''
        minute = ts.minute if ts else ''

        data.append({
            'user': r.user.username,
            'station': r.station.name,
            'year': year,
            'month': month,
            'day': day,
            'hour': hour,
            'minute': minute,
            'rainfall_mm': r.rainfall_mm,
        })

    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame(columns=['user', 'station', 'year', 'month', 'day', 'hour', 'minute', 'rainfall_mm'])

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='rainfall')

    output.seek(0)
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=rainfall_records.xlsx'
    return response


@login_required
def dashboard(request):
    """ داشبورد نمایش داده‌های ثبت شده توسط کاربر با فیلتر ایستگاه و تاریخ """
    station_filter = request.GET.get('station')
    date_filter = request.GET.get('date')

    # رکوردهای کاربر جاری
    records = RainRecord.objects.filter(user=request.user).order_by('-timestamp')

    # فیلتر بر اساس ایستگاه
    if station_filter and station_filter != 'all':
        records = records.filter(station__id=station_filter)

    # فیلتر بر اساس تاریخ شمسی
    if date_filter:
        try:
            jdate = jdatetime.datetime.strptime(date_filter, '%Y/%m/%d')
            gdate_start = jdate.togregorian().replace(hour=0, minute=0, second=0)
            gdate_end = jdate.togregorian().replace(hour=23, minute=59, second=59)
            records = records.filter(timestamp__range=(gdate_start, gdate_end))
        except Exception:
            pass  # اگر تاریخ اشتباه وارد شد، فیلتر نکن

    stations = Station.objects.all()
    return render(request, 'dashboard.html', {
        'records': records,
        'stations': stations,
        'station_filter': station_filter,
        'date_filter': date_filter
    })


@login_required
def edit_record(request, record_id):
    record = get_object_or_404(RainRecord, id=record_id, user=request.user)
    if request.method == 'POST':
        form = RainRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = RainRecordForm(instance=record)
    return render(request, 'edit_record.html', {'form': form})

@login_required
def delete_record(request, record_id):
    record = get_object_or_404(RainRecord, id=record_id, user=request.user)
    record.delete()
    return redirect('dashboard')


# helper: تبدیل ارقام فارسی/عربی به ASCII
def _normalize_digits(s: str) -> str:
    if not isinstance(s, str):
        return s
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    arabic_digits  = '٠١٢٣٤٥٦٧٨٩'
    for i, d in enumerate(persian_digits):
        s = s.replace(d, str(i))
    for i, d in enumerate(arabic_digits):
        s = s.replace(d, str(i))
    # همچنین گاهی از کاراکترهای فاصلهٔ غیرمعمول استفاده می‌شود:
    s = s.replace('\u200c', '').strip()
    return s

@login_required
@csrf_exempt
def inline_update(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'درخواست باید POST باشد'}, status=400)

    record_id = request.POST.get('id')
    field = request.POST.get('field')
    value_raw = request.POST.get('value', '')

    try:
        record = RainRecord.objects.get(id=record_id, user=request.user)
    except RainRecord.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'رکورد یافت نشد'}, status=404)

    # نرمالیزهٔ مقدار (اعداد فارسی -> انگلیسی)
    value = _normalize_digits(value_raw)

    try:
        if field == 'rainfall_mm':
            # تبدیل به float
            record.rainfall_mm = float(value)
        elif field == 'date':
            # value مانند '1403/07/25' (شمسی) است
            # زمان قبلی را نگه می‌داریم
            old_time = record.timestamp.time()
            # پارس کردن Jalali به Gregorian
            # jdatetime.datetime.strptime با فرمت '%Y/%m/%d'
            jdt = jdatetime.datetime.strptime(value, '%Y/%m/%d')
            gdate = jdt.togregorian().date()
            new_dt = datetime.combine(gdate, old_time)
            if settings.USE_TZ:
                new_dt = timezone.make_aware(new_dt, timezone.get_default_timezone())
            record.timestamp = new_dt
        elif field == 'time':
            # value مانند '17:30' یا '07:05'
            old_date = record.timestamp.date()
            # اگر اعداد فارسی بود، قبلاً نرمال شد
            # parse time (ممکن است با ':' جدا شده باشد)
            try:
                new_time = datetime.strptime(value, '%H:%M').time()
            except ValueError:
                # تلاش برای فرمت بدون صفر پیشرو (H:M)
                parts = value.split(':')
                if len(parts) == 2:
                    h = int(parts[0]) if parts[0] else 0
                    m = int(parts[1]) if parts[1] else 0
                    new_time = datetime.time(h, m)
                else:
                    raise
            new_dt = datetime.combine(old_date, new_time)
            if settings.USE_TZ:
                new_dt = timezone.make_aware(new_dt, timezone.get_default_timezone())
            record.timestamp = new_dt
        else:
            return JsonResponse({'status': 'error', 'message': 'فیلد قابل ویرایش نیست'}, status=400)

        record.save()
        return JsonResponse({'status': 'success'})

    except ValueError as ve:
        return JsonResponse({'status': 'error', 'message': f'مقدار نامعتبر: {ve}'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


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
            if user is not None:
                login(request, user)
                if not remember:
                    request.session.set_expiry(0)  # خروج خودکار پس از بستن مرورگر
                messages.success(request, f"{user.username} عزیز، خوش آمدید 🌦️")
                return redirect('dashboard')
            else:
                messages.error(request, "❌ نام کاربری یا رمز عبور اشتباه است.")
    else:
        form = LoginForm()

    return render(request, 'login.html', {'form': form})
