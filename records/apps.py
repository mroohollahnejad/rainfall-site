from django.apps import AppConfig


class RecordsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'records'

    def ready(self):
        from .models import Station
        stations = ['بندرعباس', 'بستک', 'میناب', 'بشاگرد', 'حاجی آباد']
        for s in stations:
            Station.objects.get_or_create(name=s)
