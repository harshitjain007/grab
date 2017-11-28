# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import json
import geohash
# Create your models here.

class RegionSurge(models.Model):
    geo_hash = models.CharField(max_length=32)
    demand = models.IntegerField()
    supply = models.IntegerField()
    surge = models.FloatField()

    def __str__(self):
        latlng = geohash.decode(self.geo_hash)
        ret = {
            "geo_hash":self.geo_hash,
            "demand":self.demand,
            "supply":self.supply,
            "surge":self.surge,
            "lat":latlng[0],
            "lng":latlng[1]
        }
        return json.dumps(ret)

class HourlyDemandSupply(models.Model):
    class Meta:
        unique_together = (('hour','date','geo_hash'),)

    geo_hash = models.CharField(max_length=32)
    value = models.IntegerField()
    is_demand = models.BooleanField()
    hour = models.IntegerField()
    date = models.DateField()

class HourlyWeatherData(models.Model):
    class Meta:
        unique_together = (('hour', 'date'),)

    hour = models.IntegerField()
    date = models.DateField()
    temp_celsius = models.FloatField()
    humidity_percent = models.FloatField()
    windspeed_kmph = models.FloatField()
