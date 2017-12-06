# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from models import *
from datetime import datetime
import json

def index(request):
    return JsonResponse({"A":"Hello, world. You're at the polls index."})

def get_real_time_surge(request):
    objects = RegionSurge.objects.all()
    ret = ret = [json.loads(str(obj)) for obj in objects]
    return JsonResponse(ret,safe=False)

def get_historical_surge(request):
    date = request.GET.get('date','')
    date_obj = date.split("-")
    year = int(date_obj[0])
    mm = int(date_obj[1])
    dd = int(date_obj[2])
    hh = int(date_obj[3])
    query = '''select 1 as id, geo_hash,
    count(case is_demand when True then 1 else null end) as demand,
    count(case is_demand when False then 1 else null end) as supply
    from public.data_service_demandsupply
    where extract(day from ts)='{}' and extract(month from ts)='{}' and
    extract(year from ts)='{}' and extract(hour from ts)='{}'
    group by geo_hash'''.format(dd,mm,year,hh)
    cursor = DemandSupply.objects.raw(query)
    ret = []
    for obj in cursor:
        latlng = geohash.decode(obj.geo_hash)
        ret.append({
            "lat":latlng[0],
            "lng":latlng[1],
            "demand":obj.demand,
            "supply":obj.supply
        })
    return JsonResponse(ret,safe=False)

def get_real_time_congestion(request):
    return JsonResponse()

def get_historical_congestion(request):
    return JsonResponse()

def get_weather_traffic_data(request):
    date = request.GET.get('date','')
    date_obj = date.split("-")
    year = int(date_obj[0])
    mm = int(date_obj[1])
    dd = int(date_obj[2])
    objects = HourlyWeatherData.objects.filter(date=datetime(year, mm, dd))
    ret = [str(obj) for obj in objects]
    return JsonResponse(ret,safe=False)
# Create your views here.
