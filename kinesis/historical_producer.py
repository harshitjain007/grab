import sys,time
import geohash
import json,csv
import boto3
from random import randint
import logging
from decimal import *
from datetime import datetime
from sets import Set

conf_file = open("/home/ec2-user/conf.json","r")
conf = json.loads(conf_file.read())
conf_file.close()

rds_client = psycopg2.connect(database=conf["db"], user = conf["user"],\
            password = conf["password"], host = conf["host"], port = conf["port"])

def writeToDB(rec_list):
    cur = rds_client.cursor()

    logger.info("Inserting the records into the table...")
    query = "INSERT INTO public.data_service_demand_supply (lat,lng,geo_hash,is_demand,ts) VALUES (%s,%s,%s,%s,%s)"

    ctr = 0
    for rec in rec_list:
        is_demand = True if randint(0,1)==0 else False
        cur.execute(query,(rec["lat"],rec["lng"],rec["hash"],is_demand,rec["ts"]))
        ctr += 1
        if ctr%50==0:
            rds_client.commit()
    rds_client.commit()
    sys.exit(0)

def dd(x):
    if x<10: return "0"+str(x)
    else: return str(x)

if __name__ == "__main__":
    total_params = 1
    params_given = len(sys.argv)
    if params_given != total_params+1:
        logger.error("Missing arguments. Required {} given {}".format(total_params,params_given))
        sys.exit(2)

    skip_header = True
    in_csv = sys.argv[1]

    m=0
    h=0
    d=1
    with open(in_csv, "rbU") as f:
        reader = csv.reader(f)
        if skip_header: next(reader, None)

        rows=randint(500,700)
        rec_list=[]
        for row in reader:
            hash_value = geohash.encode(Decimal(row[5]), Decimal(row[6]), 6)
            pay_load = {
                "hash":hash_value, "lat":row[5],"long":row[6],
                "ts":"{}-{}-{} {}:{}:{}".format(2017,11,dd(d),dd(h),dd(randint(m,m+10)),randint(10,59))
                }
            rec_list.append(pay_load)
            rows -= 1

            if rows==0:
                writeToDB(rec_list)
                m+=10
                if m==60:h,m=h+1,0
                if h==24:d,h=d+1,0
                if d==31:sys.exit(0)
                rec_list = []
                rows = randint(500,700)
