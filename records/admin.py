from django.contrib import admin
from .models import Station, RainRecord


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(RainRecord)
class RainRecordAdmin(admin.ModelAdmin):
    list_display = ('station', 'timestamp', 'rainfall_mm', 'user')
    list_filter = ('station', 'user')
    search_fields = ('station__name',)
    ordering = ('-timestamp',)
