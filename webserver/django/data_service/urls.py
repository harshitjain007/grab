from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^surge/realtime',views.get_real_time_surge),
    url(r'^surge/historical',views.get_historical_surge),
    url(r'^congestion/realtime',views.get_real_time_congestion),
    url(r'^congestion/historical',views.get_historical_congestion),
    url(r'^weather',views.get_weather_traffic_data),
    url(r'^$', views.index, name='index'),
]
