# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse,JsonResponse
from data_service import models

def index(request):
    return JsonResponse({"A":"Hello, world. You're at the polls index."})

def get_real_time_surge(request):
    objects = Region_Surge.objects.all()
    ret = []
    for obj in objects:
        ret_dict = {}
        ret_dict["geo_hash"]

def get_historical_surge(request):
    return JsonResponse()

def get_real_time_congesion(request):
    return JsonResponse()

def get_historical_surge(request):
    return JsonResponse()

def get_weather_traffic_data(request):
    #get hourly demand
    #get hourly supply
    return JsonResponse()
    #fetch
# Create your views here.
