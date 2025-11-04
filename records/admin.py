from django.contrib import admin
from .models import Station, RainRecord

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'location')
    search_fields = ('name', 'code', 'location')
    ordering = ('name',)

@admin.register(RainRecord)
class RainRecordAdmin(admin.ModelAdmin):
    list_display = ('station', 'timestamp', 'rainfall_mm')
    list_filter = ('station',)
    search_fields = ('station__name',)
    ordering = ('-timestamp',)
