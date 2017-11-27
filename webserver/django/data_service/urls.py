from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^surge/realtime',views.get_real_time_surge),
    url(r'^surge/historical',views.get_historical_surge),
    url(r'^congesion/realtime',views.get_real_time_congesion),
    url(r'^congesion/historical',views.get_historical_congesion),
    url(r'^weather',views.get_weather_traffic_data)
    url(r'^$', views.index, name='index'),
]
