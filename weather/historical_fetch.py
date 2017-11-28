import json
import requests
import psycopg2

conf_file = open("/home/ec2-user/conf.json","r")
conf = json.loads(conf_file.read())
conf_file.close()

rds_client = psycopg2.connect(database=conf["db"], user = conf["user"],\
            password = conf["password"], host = conf["host"], port = conf["port"])
hist_data_url = "http://api.wunderground.com/api/b44e472e7b8b1828/history_201711{}/q/NY/New_York.json"

last_dt = 9
cur = rds_client.cursor()

for i in range(10,28):
    resp = requests.post(hist_data_url.format(i))
    payload = json.loads(resp.content)
    hourly_data = payload["history"]["observations"]
    for data in hourly_data:
        dt = "2017-11-"+str(i)
        hour = data["utcdate"]["hour"]
        temp = data["tempm"]
        humi = data["hum"]
        wspd = data["wspdm"]
        query = "insert into public.data_service_hourlyweatherdata \
        (hour,date,temp_celsius,humidity_percent,windspeed_kmph) values \
        ({},{},{},{},{}) on conflict do nothing".format(hour,dt,temp,humi,wspd)
        cur.execute(query)
    rds_client.commit()
