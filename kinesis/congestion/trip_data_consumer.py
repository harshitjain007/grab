import sys,time
import json
import boto3
import copy
import math
import logging
import psycopg2
from decimal import *
from random import randint
from datetime import datetime, timedelta

conf_file = open("/home/ec2-user/.conf/db_config.json","r")
conf = json.loads(conf_file.read())
conf_file.close()

rds_client = psycopg2.connect(database=conf["db"], user = conf["user"],\
            password = conf["password"], host = conf["host"], port = conf["port"])
kinesis_client = boto3.client("kinesis")
logger = None

def getList(rec_list,end_time):
    store_list = []
    for rec in rec_list:
        data = json.loads(rec["Data"])
        ts = datetime.strptime(data["ts"],"%Y-%m-%d %H:%M:%S")
        if ts > end_time: return store_list
        store_list.append({
            "lat":data["lat"], "lng":data["long"], "ts":ts
        })
    return store_list

def fetchAndStoreRecords(queue_name,start_time,end_time):
    stream_info = kinesis_client.describe_stream(StreamName=queue_name)
    shard_id = stream_info["StreamDescription"]["Shards"][0]["ShardId"]
    logger.info("shard_id:{} ".format(shard_id))

    shard_itr = kinesis_client.get_shard_iterator(
        StreamName=queue_name,
        ShardId=shard_id,
        ShardIteratorType="AT_TIMESTAMP",
        Timestamp=start_time
        )
    shard_itr_cd = shard_itr["ShardIterator"]
    resp = kinesis_client.get_records(ShardIterator=shard_itr_cd, Limit=100)

    store_list = getList(resp["Records"],end_time)
    if len(store_list)!=0: writeToDB(store_list)

    total_rec_cnt = len(resp["Records"])
    logger.info("Total records fetched:{}".format(total_rec_cnt))

    empty_fetch_cnt=0
    while resp["NextShardIterator"] is not None:
        shard_itr_cd = resp["NextShardIterator"]
        time.sleep(0.5)
        resp = kinesis_client.get_records(ShardIterator=shard_itr_cd,Limit=100)

        rec_cnt = len(resp["Records"])
        if rec_cnt==0:
            empty_fetch_cnt+=1
            if empty_fetch_cnt==10: return

        else: total_rec_cnt+=rec_cnt
        logger.info("Total records fetched:{}".format(total_rec_cnt))

        r_list = getList(resp["Records"],end_time)
        if len(r_list)!=0: writeToDB(r_list)

def writeToDB(rec_list):
    cur = rds_client.cursor()

    logger.info("Inserting the {} records into the table...".format(len(rec_list)))
    query = "INSERT INTO public.data_service_tripendstats (lat,lng,is_start,ts) VALUES (%s,%s,%s,%s)"

    ctr = 0
    for rec in rec_list:
        is_start = True if randint(0,1)==0 else False
        cur.execute(query,(rec["lat"],rec["lng"],is_start,rec["ts"]))
        ctr += 1
        if ctr%50==0:rds_client.commit()
    rds_client.commit()

if __name__ == "__main__":
    total_params = 3
    params_given = len(sys.argv)
    if params_given-1 != total_params:
        print("Missing arguments. Required {} given {}".format(total_params,params_given-1))
        sys.exit(2)

    trip_queue = sys.argv[1]
    agg_interval = int(sys.argv[2])
    log_file = sys.argv[3]

    logging.basicConfig(filename=log_file,format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)
    logger=logging.getLogger(__name__)

    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=agg_interval)

    logger.info("Fetching records...")
    fetchAndStoreRecords(trip_queue,start_time,end_time)

    logger.info("================================\n")
