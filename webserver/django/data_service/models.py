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
    surge = models.DecimalField(max_digits=5,decimal_places=2)

    def __str__(self):
        latlng = geohash.decode(self.geo_hash)
        ret = {
            "geo_hash":self.geo_hash,
            "demand":self.demand,
            "supply":self.supply,
            "surge":str(self.surge),
            "lat":latlng[0],
            "lng":latlng[1]
        }
        return json.dumps(ret)

class HourlyDemandSupply(models.Model):
    geo_hash = models.CharField(max_length=32)
    value = models.IntegerField()
    is_demand = models.BooleanField()
    hour = models.IntegerField()
    date = models.DateField()

