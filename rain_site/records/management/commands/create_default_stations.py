
from django.core.management.base import BaseCommand
from records.models import Station

class Command(BaseCommand):
    help = 'Create default stations'

    def handle(self, *args, **options):
        names = ['بستک', 'بندرعباس', 'میناب', 'بشاگرد', 'حاجی\u200cآباد']
        for n in names:
            Station.objects.get_or_create(name=n)
        self.stdout.write(self.style.SUCCESS('Default stations created'))
