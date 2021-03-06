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
logger = None

def populateCount(geo_dict,rec_list,end_time):
    for rec in rec_list:
        data = json.loads(rec["Data"])
        ts = datetime.strptime(data["ts"],"%Y-%m-%d %H:%M:%S")
        if ts > end_time: return False
        geo_dict[data["hash"]] = geo_dict[data["hash"]]+1 if data["hash"] in geo_dict else 1
    return True

def fetchAndAggregateRecords(queue_name,start_time,end_time):
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

def surge(demand,supply,max_surge):
    coeff = 1-max_surge
    x = float(demand)/float(supply)
    return max_surge + coeff * math.exp((1-x)/2)

def computeAreawiseSurge(geo_demand,geo_supply,max_surge):
    surge_dict = {}
    area_list = list(set(geo_demand.keys()+geo_supply.keys()))
    for area_hash in area_list:
        if area_hash not in geo_supply:
            surge_dict[area_hash] = max_surge
        elif area_hash not in geo_demand:
            surge_dict[area_hash] = 0
        else:
            surge_dict[area_hash] = surge(geo_demand[area_hash],geo_supply[area_hash],max_surge)
    return surge_dict

def updateSurgeTable(geo_surge,geo_demand,geo_supply):
    surge_table = "public.data_service_regionsurge"

    logger.info("Truncating the table...")
    cur = rds_client.cursor()
    cur.execute("TRUNCATE {};".format(surge_table))
    rds_client.commit()
    logger.info("Table truncated successfully.")

    logger.info("Inserting the records into the table...")
    ctr = 0
    for area_hash in geo_surge:
        supply = geo_supply[area_hash] if area_hash in geo_supply else 0
        demand = geo_demand[area_hash] if area_hash in geo_demand else 0
        cur.execute("INSERT INTO {} (geo_hash,demand,supply,surge) VALUES ('{}',\
        {},{},{})".format(surge_table,area_hash, demand, supply, geo_surge[area_hash]))
        ctr += 1
        if ctr%50==0:
            rds_client.commit()
            logger.info("Total records inserted:{}".format(ctr))
    rds_client.commit()

if __name__ == "__main__":
    total_params = 5
    params_given = len(sys.argv)
    if params_given != total_params+1:
        print("Missing arguments. Required {} given {}".format(total_params,params_given))
        sys.exit(2)

    demand_queue = sys.argv[1]
    supply_queue = sys.argv[2]
    agg_interval = int(sys.argv[3])
    max_surge = int(sys.argv[4])
    log_file = sys.argv[5]

    logging.basicConfig(filename=log_file,format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)
    logger=logging.getLogger(__name__)

    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=agg_interval)

    logger.info("Fetching demand records...")
    geo_demand = fetchAndAggregateRecords(demand_queue,start_time,end_time)
    logger.info("Total {} demand records fetched for {} geo_areas".format(sum(geo_demand.values()),len(geo_demand)))

    logger.info("Fetching supply records...")
    geo_supply = fetchAndAggregateRecords(supply_queue,start_time,end_time)
    logger.info("Total {} supply records fetched for {} geo_areas".format(sum(geo_supply.values()),len(geo_supply)))

    logger.info("Calculating surge for the areas...")
    geo_surge = computeAreawiseSurge(geo_demand,geo_supply,max_surge)
    logger.info("Surge calculation complete.")

    logger.info("Updating the surge table with {} records...".format(len(geo_surge)))
    updateSurgeTable(geo_surge,geo_demand,geo_supply)
    logger.info("Surge table updated successfully.")

    logger.info("================================\n")
