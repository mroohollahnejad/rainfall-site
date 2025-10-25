
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
        return f"{self.station} - {self.timestamp} - {self.rainfall_mm}"

