#!/usr/bin/env python3
"""
این اسکریپت یک سایت جنگو را به صورت خودکار می‌سازد که ویژگی‌های خواسته‌شده را دارد:
- رجیستر/لاگین کاربر
- وارد کردن داده‌های بارندگی هر 3 ساعته برای ایستگاه‌های از پیش تعریف‌شده (بستک، بندرعباس، میناب، بشاگرد، حاجی‌آباد)
- تاریخ به صورت شمسی (جلالی) وارد می‌شود (سال، ماه، روز، ساعت، دقیقه)
- خروجی تمامی داده‌ها به یک فایل اکسل

نکته: اسکریپت محیط محلی شما را پیکربندی نمی‌کند مگر اینکه اجازه نصب پکیج‌ها (pip) و اجرای دستورات django-admin را داشته باشید.

نحوه اجرا:
1. این فایل را ذخیره کنید (مثلاً django_rain_site_generator.py)
2. در ترمینال/کامندپرامپت در پوشه‌ای که می‌خواهید پروژه ساخته شود اجرا کنید:
   python django_rain_site_generator.py

اسکریپت پکیج‌های مورد نیاز را نصب می‌کند، یک پروژه جنگو به نام "rain_site" و یک اپ به نام "records" می‌ساازد، فایل‌های مدل، فرم، ویو، قالب‌ها و آدرس‌ها را می‌نویسد و یک گروه از ایستگاه‌های پیش‌فرض را اضافه می‌کند.

بعد از اجرای اسکریپت، برای شروع سرور:
  cd rain_site
  python manage.py migrate
  python manage.py createsuperuser  # اگر خواستید
  python manage.py runserver

سپس به http://127.0.0.1:8000/ بروید.

"""

import os
import sys
import subprocess
import textwrap
from pathlib import Path

PROJECT_NAME = "rain_site"
APP_NAME = "records"
BASE_DIR = Path.cwd() / PROJECT_NAME

REQUIREMENTS = [
    "django>=4.2",
    "jdatetime",
    "openpyxl",
    "pandas",
]

STATIONS = [
    "بستک",
    "بندرعباس",
    "میناب",
    "بشاگرد",
    "حاجی‌آباد",
]


def run(cmd, cwd=None, check=True):
    print(f">>> {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd, check=check)


def install_requirements():
    print("Installing required packages with pip...")
    run([sys.executable, "-m", "pip", "install"] + REQUIREMENTS)


def start_django_project():
    if BASE_DIR.exists():
        print(f"Directory {BASE_DIR} already exists. Aborting to avoid overwriting.")
        sys.exit(1)

    print("Creating Django project and app...")
    run([sys.executable, "-m", "django", "startproject", PROJECT_NAME, "."], cwd=Path.cwd())

    # create app
    run([sys.executable, "manage.py", "startapp", APP_NAME], cwd=Path.cwd())


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")


def patch_settings():
    settings_path = BASE_DIR / "settings.py"
    s = settings_path.read_text(encoding="utf-8")

    # add app and jdatetime to INSTALLED_APPS + static templates localization settings
    s = s.replace("INSTALLED_APPS = [",
                  "INSTALLED_APPS = [\n    'django.contrib.humanize',\n    'django.contrib.sites',\n    'django.contrib.messages',\n    'django.contrib.staticfiles',\n    'django.contrib.sessions',\n    'django.contrib.admin',\n    'django.contrib.auth',\n    f'\n    \"{APP_NAME}\",\n'")

    # Simpler: inject APP_NAME into INSTALLED_APPS properly
    s = s.replace("INSTALLED_APPS = [\n    'django.contrib.admin',",
                  "INSTALLED_APPS = [\n    'django.contrib.admin',\n    'django.contrib.auth',\n    'django.contrib.contenttypes',\n    'django.contrib.sessions',\n    'django.contrib.messages',\n    'django.contrib.staticfiles',\n    '{app}',".format(app=APP_NAME))

    # Add templates DIR and static settings
    if "STATIC_URL" not in s:
        s += "\n\n# Static settings\nSTATIC_URL = '/static/'\nSTATICFILES_DIRS = [BASE_DIR / 'static']\n\n"

    # add time zone and language code - keep generic
    s = s.replace("LANGUAGE_CODE = 'en-us'", "LANGUAGE_CODE = 'fa'")
    s = s.replace("TIME_ZONE = 'UTC'", "TIME_ZONE = 'Asia/Tehran'")

    write_file(settings_path, s)


def create_models():
    content = textwrap.dedent(f"""
    from django.db import models
    from django.contrib.auth.models import User
    import jdatetime
    
    class Station(models.Model):
        name = models.CharField(max_length=100, unique=True)

        def __str__(self):
            return self.name

    class RainRecord(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        station = models.ForeignKey(Station, on_delete=models.PROTECT)
        # We'll store datetime in Gregorian internally, but allow users to input Jalali
        timestamp = models.DateTimeField()
        rainfall_mm = models.FloatField()

        created_at = models.DateTimeField(auto_now_add=True)

        def __str__(self):
            return f"{{self.station}} - {{self.timestamp}} - {{self.rainfall_mm}}"

    """)
    write_file(BASE_DIR / APP_NAME / "models.py", content)


def create_forms():
    content = textwrap.dedent("""
    from django import forms
    import jdatetime
    from .models import RainRecord, Station

    class RainRecordForm(forms.ModelForm):
        # separate jalali fields for user-friendly input
        jy = forms.IntegerField(label='سال (شمسی)')
        jm = forms.IntegerField(label='ماه (شمسی)')
        jd = forms.IntegerField(label='روز (شمسی)')
        hour = forms.IntegerField(label='ساعت', min_value=0, max_value=23)
        minute = forms.IntegerField(label='دقیقه', min_value=0, max_value=59)

        class Meta:
            model = RainRecord
            fields = ['station', 'rainfall_mm']

        def clean(self):
            cleaned = super().clean()
            jy = cleaned.get('jy')
            jm = cleaned.get('jm')
            jd = cleaned.get('jd')
            hour = cleaned.get('hour')
            minute = cleaned.get('minute')
            try:
                jalali = jdatetime.datetime(jy, jm, jd, hour, minute)
                greg = jalali.togregorian()
                cleaned['timestamp'] = greg
            except Exception as e:
                raise forms.ValidationError('تاریخ یا زمان نامعتبر است: ' + str(e))
            return cleaned

        def save(self, commit=True):
            obj = super().save(commit=False)
            obj.timestamp = self.cleaned_data['timestamp']
            if commit:
                obj.save()
            return obj
    """)
    write_file(BASE_DIR / APP_NAME / "forms.py", content)


def create_views():
    content = textwrap.dedent("""
    from django.shortcuts import render, redirect
    from django.contrib.auth import login, authenticate, logout
    from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
    from django.contrib.auth.decorators import login_required
    from django.http import HttpResponse
    import pandas as pd
    from .models import RainRecord, Station
    from .forms import RainRecordForm

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
    """)
    write_file(BASE_DIR / APP_NAME / "views.py", content)


def create_urls():
    content_app = textwrap.dedent("""
    from django.urls import path
    from . import views

    urlpatterns = [
        path('', views.index, name='index'),
        path('register/', views.register_view, name='register'),
        path('login/', views.login_view, name='login'),
        path('logout/', views.logout_view, name='logout'),
        path('enter/', views.enter_record, name='enter'),
        path('export/', views.export_excel, name='export'),
    ]
    """)
    write_file(BASE_DIR / APP_NAME / "urls.py", content_app)

    # project urls
    proj_urls_path = BASE_DIR / "urls.py"
    proj_urls = textwrap.dedent(f"""
    from django.contrib import admin
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('', include('{APP_NAME}.urls')),
    ]
    """.format(APP_NAME=APP_NAME))
    write_file(proj_urls_path, proj_urls)


def create_templates():
    base = textwrap.dedent("""
    <!doctype html>
    <html lang="fa" dir="rtl">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>سامانه ورود بارش</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
      <div class="container">
        <a class="navbar-brand" href="/">ورود بارش</a>
        <div>
          {% if user.is_authenticated %}
            <a class="btn btn-outline-primary btn-sm" href="/enter/">ثبت</a>
            <a class="btn btn-outline-danger btn-sm" href="/logout/">خروج</a>
          {% else %}
            <a class="btn btn-outline-success btn-sm" href="/login/">ورود</a>
            <a class="btn btn-outline-secondary btn-sm" href="/register/">ثبت نام</a>
          {% endif %}
        </div>
      </div>
    </nav>
    <div class="container mt-4">
      {% block content %}{% endblock %}
    </div>
    </body>
    </html>
    """)

    index = textwrap.dedent("""
    {% extends 'base.html' %}
    {% block content %}
    <div class="card p-4">
      <h3>به سامانه ورود بارش خوش آمدید</h3>
      <p>برای وارد کردن داده‌ها وارد شوید.</p>
    </div>
    {% endblock %}
    """)

    register = textwrap.dedent("""
    {% extends 'base.html' %}
    {% block content %}
    <div class="card p-4">
      <h4>ثبت نام</h4>
      <form method="post">{% csrf_token %}
        {{ form.as_p }}
        <button class="btn btn-primary">ثبت</button>
      </form>
    </div>
    {% endblock %}
    """)

    login = textwrap.dedent("""
    {% extends 'base.html' %}
    {% block content %}
    <div class="card p-4">
      <h4>ورود</h4>
      <form method="post">{% csrf_token %}
        {{ form.as_p }}
        <button class="btn btn-primary">ورود</button>
      </form>
    </div>
    {% endblock %}
    """)

    enter = textwrap.dedent("""
    {% extends 'base.html' %}
    {% block content %}
    <div class="card p-4">
      <h4>ثبت رکورد بارش</h4>
      {% if success %}
        <div class="alert alert-success">رکورد با موفقیت ذخیره شد.</div>
      {% endif %}
      <form method="post">{% csrf_token %}
        {{ form.station.label_tag }}
        {{ form.station }}
        <div class="row">
          <div class="col">
            {{ form.jy.label_tag }}
            {{ form.jy }}
          </div>
          <div class="col">
            {{ form.jm.label_tag }}
            {{ form.jm }}
          </div>
          <div class="col">
            {{ form.jd.label_tag }}
            {{ form.jd }}
          </div>
        </div>
        <div class="row mt-2">
          <div class="col">
            {{ form.hour.label_tag }}
            {{ form.hour }}
          </div>
          <div class="col">
            {{ form.minute.label_tag }}
            {{ form.minute }}
          </div>
        </div>
        <div class="mt-2">
          {{ form.rainfall_mm.label_tag }}
          {{ form.rainfall_mm }}
        </div>
        <button class="btn btn-primary mt-2">ذخیره</button>
      </form>
      <hr />
      <a class="btn btn-outline-secondary" href="/export/">دانلود همه داده‌ها (Excel)</a>
    </div>
    {% endblock %}
    """)

    templates_dir = BASE_DIR / APP_NAME / "templates"
    write_file(templates_dir / "base.html", base)
    write_file(templates_dir / "index.html", index)
    write_file(templates_dir / "register.html", register)
    write_file(templates_dir / "login.html", login)
    write_file(templates_dir / "enter.html", enter)


def create_admin():
    content = textwrap.dedent("""
    from django.contrib import admin
    from .models import Station, RainRecord

    @admin.register(Station)
    class StationAdmin(admin.ModelAdmin):
        list_display = ('name',)

    @admin.register(RainRecord)
    class RainRecordAdmin(admin.ModelAdmin):
        list_display = ('station','timestamp','rainfall_mm','user')
        list_filter = ('station', 'user')
    """)
    write_file(BASE_DIR / APP_NAME / "admin.py", content)


def create_migrations_and_initial_data():
    # We'll add a small data migration script to create default stations
    init_script = textwrap.dedent(f"""
    from django.core.management.base import BaseCommand
    from {APP_NAME}.models import Station

    class Command(BaseCommand):
        help = 'Create default stations'

        def handle(self, *args, **options):
            names = {STATIONS!r}
            for n in names:
                Station.objects.get_or_create(name=n)
            self.stdout.write(self.style.SUCCESS('Default stations created'))
    """)
    mgmt_dir = BASE_DIR / APP_NAME / "management" / "commands"
    mgmt_dir.mkdir(parents=True, exist_ok=True)
    write_file(mgmt_dir / "create_default_stations.py", init_script)


def update_project_init():
    # ensure project __init__ exists (it does), and make small urls change already done
    pass


def main():
    install_requirements()
    start_django_project()
    patch_settings()
    create_models()
    create_forms()
    create_views()
    create_urls()
    create_templates()
    create_admin()
    create_migrations_and_initial_data()

    print("\nتمام فایل‌ها نوشته شدند. اکنون دستورات زیر را اجرا کنید:\n")
    print("cd {}".format(BASE_DIR))
    print("python manage.py makemigrations")
    print("python manage.py migrate")
    print("python manage.py create_default_stations")
    print("python manage.py createsuperuser")
    print("python manage.py runserver")

if __name__ == '__main__':
    main()
