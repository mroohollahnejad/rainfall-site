from django.core.management.base import BaseCommand
from records.models import Station

class Command(BaseCommand):
    help = 'ایجاد ایستگاه‌های پیش‌فرض'

    def handle(self, *args, **kwargs):
        stations = ['بستک', 'بندرعباس', 'میناب', 'بشاگرد', 'حاجی آباد']
        for s in stations:
            obj, created = Station.objects.get_or_create(name=s)
            if created:
                self.stdout.write(self.style.SUCCESS(f'ایستگاه "{s}" ایجاد شد.'))
            else:
                self.stdout.write(f'ایستگاه "{s}" قبلاً وجود داشت.')
        self.stdout.write(self.style.SUCCESS('تمام ایستگاه‌های پیش‌فرض بررسی شدند.'))
