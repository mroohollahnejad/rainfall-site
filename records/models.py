from django.db import models
from django.contrib.auth.models import User

class Station(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class RainRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    rainfall_mm = models.FloatField()

    def __str__(self):
        return f"{self.station} - {self.timestamp} - {self.rainfall_mm}mm"
