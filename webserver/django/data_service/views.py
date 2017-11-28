# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from models import *
from datetime import datetime


def index(request):
    return JsonResponse({"A":"Hello, world. You're at the polls index."})

def get_real_time_surge(request):
    objects = RegionSurge.objects.all()
    ret = [str(obj) for obj in objects]
    return JsonResponse(ret,safe=False)

def get_historical_surge(request):
    return JsonResponse()

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
