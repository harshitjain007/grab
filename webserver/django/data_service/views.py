# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse,JsonResponse


def index(request):
    return JsonResponse({"A":"Hello, world. You're at the polls index."})
# Create your views here.
