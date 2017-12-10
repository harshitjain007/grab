from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse,JsonResponse


def index(request):
    return render(request, 'index.html')

def surge(request):
    return render(request, 'surge.html')

def congestion(request):
    return render(request, 'congestion.html')

def weather(request):
    return render(request, 'weather.html')

def architecture(request):
    return render(request, 'architecture.html')
