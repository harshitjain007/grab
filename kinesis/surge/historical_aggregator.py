import sys,time
import geohash
import json
import boto3
import copy
import math
import logging
import psycopg2
from decimal import *
from datetime import datetime, timedelta

conf_file = open("/home/ec2-user/.conf/db_config.json","r")
conf = json.loads(conf_file.read())
conf_file.close()

rds_client = psycopg2.connect(database=conf["db"], user = conf["user"],\
            password = conf["password"], host = conf["host"], port = conf["port"])
kinesis_client = boto3.client("kinesis")

#logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def populateCount(geo_dict,rec_list,end_time):
    for rec in rec_list:
        data = json.loads(rec["Data"])
        ts = datetime.strptime(data["ts"],"%Y-%m-%d %H:%M:%S")
        if ts > end_time: return False
        geo_dict[data["hash"]] = geo_dict[data["hash"]]+1 if data["hash"] in geo_dict else 1
    return True

def fetchAndAggRecords(queue_name,start_time,end_time):
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

    geo_dict = {}
    if not populateCount(geo_dict,resp["Records"],end_time):return geo_dict

    total_rec_cnt = len(resp["Records"])
    while resp["NextShardIterator"] is not None:
        shard_itr_cd = resp["NextShardIterator"]
        time.sleep(0.5)
        resp = kinesis_client.get_records(ShardIterator=shard_itr_cd,Limit=100)

        rec_cnt = len(resp["Records"])
        if rec_cnt==0:return geo_dict
        else: total_rec_cnt+=rec_cnt
        logger.info("Total records fetched:{}".format(total_rec_cnt))

        if not populateCount(geo_dict,resp["Records"],end_time):return geo_dict

    return geo_dict

def updateHourlyDemandSupplyTable(geo_dict,is_demand,start_time):
    table = "public.data_service_hourly_demand_supply"

    logger.info("Inserting the records into {} table...".format(hourly_table))
    ctr = 0
    for area_hash in geo_dict:
        cur.execute("INSERT INTO {} (geo_hash,value,is_demand,date,hour) VALUES ('{}',{},{})"\
        .format(table,area_hash,geo_dict[area_hash],is_demand, ,)
        ctr += 1
        if ctr%50==0:
            rds_client.commit()
            logger.info("Total records inserted:{}".format(ctr))
    rds_client.commit()

if __name__ == "__main__":
    total_params = 4
    params_given = len(sys.argv)
    if params_given != total_params+1:
        logger.error("Missing arguments. Required {} given {}".format(total_params,params_given))
        sys.exit(2)

    demand_queue = sys.argv[1]
    supply_queue = sys.argv[2]
    run_freq = int(sys.argv[3])
    agg_interval = int(sys.argv[4])

    while True:
        end_time = datetime.now()
        start_time = now - timedelta(minutes=agg_interval)

        logger.info("Fetching demand records...")
        geo_demand = fetchAndAggRecords(demand_queue,start_time,end_time)
        logger.info("Total {} demand records fetched for {} geo_areas".\
                                format(sum(geo_demand.values()),len(geo_demand)))

        logger.info("Fetching supply records...")
        geo_supply = fetchAndAggRecords(supply_queue,start_time,end_time)
        logger.info("Total {} supply records fetched for {} geo_areas".\
                                format(sum(geo_supply.values()),len(geo_supply)))

        logger.info("Updating demand supply table with {} records...".format(len(geo_surge)))
        updateHourlyDemandSupplyTable(geo_demand,True)
        updateHourlyDemandSupplyTable(geo_supply,False)
        logger.info("HourlyDemand_Supply table updated successfully.")

        logger.info("Sleeping for {} seconds...".format(run_freq))
        time.sleep(run_freq)
