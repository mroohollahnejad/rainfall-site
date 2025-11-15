from django.contrib import admin
from .models import Station, RainRecord

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(RainRecord)
class RainRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'station', 'timestamp', 'time_range', 'rainfall_mm')
    list_filter = ('station','time_range','timestamp','user')
    search_fields = ('station__name','time_range')
    ordering = ['-timestamp']
    date_hierarchy = 'timestamp'
