import json
import requests
import psycopg2
import datetime

conf_file = open("/home/ec2-user/conf.json","r")
conf = json.loads(conf_file.read())
conf_file.close()

hist_data_url = "http://api.wunderground.com/api/b44e472e7b8b1828/history_{}/q/NY/New_York.json"
rds_client = psycopg2.connect(database=conf["db"], user=conf["user"],\
            password=conf["password"], host=conf["host"], port=conf["port"])
cur = rds_client.cursor()

now = datetime.datetime.now()
yesterday = now - datetime.timedelta(hours=24)

resp = requests.post(hist_data_url.format(yesterday.strftime("%Y%m%d")))
payload = json.loads(resp.content)
hourly_data = payload["history"]["observations"]
for data in hourly_data:
    dt = datetime.date(yesterday.year,yesterday.month,yesterday.day)
    hour = int(data["utcdate"]["hour"])
    temp = data["tempm"]
    humi = None if data["hum"]=="N/A" else data["hum"]
    wspd = data["wspdm"]
    query = "insert into public.data_service_hourlyweatherdata \
    (hour,date,temp_celsius,humidity_percent,windspeed_kmph) values \
    (%s,%s,%s,%s,%s) on conflict do nothing"
    cur.execute(query,(hour,dt,temp,humi,wspd))
rds_client.commit()

