import json
import requests
import psycopg2
from datetime import datetime,timedelta

conf_file = open("/home/ec2-user/conf.json","r")
conf = json.loads(conf_file.read())
conf_file.close()

hist_data_url = "http://api.wunderground.com/api/b44e472e7b8b1828/history_{}/q/NY/New_York.json"
rds_client = psycopg2.connect(database=conf["db"], user=conf["user"],\
            password=conf["password"], host=conf["host"], port=conf["port"])
cur = rds_client.cursor()

now = datetime.now()
yesterday = now - timedelta(hours=24)

resp = requests.post(hist_data_url.format(yesterday.strftime("%Y%m%d")))
payload = json.loads(resp.content)
hourly_data = payload["history"]["observations"]
for data in hourly_data:
    dt = yesterday.strftime("%Y-%m-%d")
    hour = data["utcdate"]["hour"]
    temp = data["tempm"]
    humi = data["hum"]
    wspd = data["wspdm"]
    print dt,hour,temp,humi,wspd
    query = "insert into public.data_service_hourlyweatherdata \
    (hour,date,temp_celsius,humidity_percent,windspeed_kmph) values \
    ({},{},{},{},{}) on conflict do nothing".format(hour,dt,temp,humi,wspd)
    cur.execute(query)
rds_client.commit()
