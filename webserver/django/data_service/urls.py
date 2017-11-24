from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^surge/realtime',view.get_real_time_surge),
    url(r'^surge/historical',view.get_historical_surge),
    url(r'^congesion/realtime',view.get_real_time_congesion),
    url(r'^congesion/historical',view.get_historical_congesion),
    url(r'^$', views.index, name='index'),
]
