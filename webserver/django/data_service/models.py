# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
import json
# Create your models here.

class RegionSurge(models.Model):
    geo_hash = models.CharField(max_length=32)
    demand = models.IntegerField()
    supply = models.IntegerField()
    surge = models.DecimalField(max_digits=5,decimal_places=2)

    def __str__(self):
        ret = {
            "geo_hash":self.geo_hash,
            "demand":self.demand,
            "supply":self.supply,
            "surge":self.surge
        }
        return json.dumps(ret)
    
class HourlyDemandSupply(models.Model):
    geo_hash = models.CharField(max_length=32)
    value = models.IntegerField()
    is_demand = models.BooleanField()
    hour = models.IntegerField()
    date = models.DateField()
