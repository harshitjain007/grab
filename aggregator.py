import sys,time
import geohash
import json
import boto3
import copy
import math
import psycopg2
from decimal import *
from datetime import datetime, timedelta

kinesis_client = boto3.client("kinesis")
conf = json.loads()
rds_client = psycopg2.connect(database=conf["db"], user = conf["user"],\
            password = conf["password"], host = conf["host"], port = conf["port"])

#logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def populate_count(geo_dict,rec_list,timestamp):
    for rec in rec_list:
        data = json.loads(rec["Data"])
        ts = datetime.strptime(data["ts"],"%Y-%m-%d %H:%M:%S")
        if ts > timestamp: return False
        geo_dict[data["hash"]] = geo_dict[data["hash"]]+1 if data["hash"] in geo_dict else 1
    return True

def fetchRecords(queue_name,timestamp,agg_interval):
    shard_itr = kinesis_client.get_shard_iterator(
        StreamName=queue_name,
        ShardId="shardId-000000000000",
        ShardIteratorType="AT_TIMESTAMP",
        Timestamp=timestamp-timedelta(minutes=agg_interval)
        )
    shard_itr_cd = shard_itr["ShardIterator"]
    resp = kinesis_client.get_records(ShardIterator=shard_itr_cd, Limit=100)

    geo_dict = {}
    if len(resp["Records"])>0:
        if not populate_count(geo_dict,res["Records"],timestamp):
            return geo_dict

    while resp["NextShardIterator"] is not None:
        shard_itr_cd = resp["NextShardIterator"]
        resp = kinesis_client.get_records(ShardIterator=shard_itr_cd,Limit=100)
        if len(resp["Records"])>0:
            if not populate_count(geo_dict,res["Records"],timestamp):
                return geo_dict

    return geo_dict

def compute_surge(geo_demand,geo_supply,max_surge):
    surge_dict = copy.deepcopy(geo_demand)
    coeff = max_surge-1
    for area_hash in surge_dict:
        if area_hash not in geo_supply:
            surge_dict[area_hash] = max_surge
        elif geo_supply[area_hash]<surge_dict[area_hash]:
            surge_dict[area_hash] = 1 + coeff*math.atan(surge_dict[area_hash]/geo_supply[area_hash])
        else:
            surge_dict.remove(area_hash)
    return surge_dict

def update_surge_table(geo_surge):
    cur = rds_client.cursor()
    cur.execute("TRUNCATE v1.geo_area_surge;")
    rds_client.commit()

    ctr = 0
    for area_hash in geo_surge:
        cur.execute("INSERT INTO v1.geo_area_surge (geo_hash, surge) VALUES ({},{})".format(area_hash, geo_surge[area_hash]))
        ctr = ctr + 1
        if ctr%10==0:
             rds_client.commit()
    rds_client.commit()

if __name__ == "__main__":
    if len(sys.argv) != 6:
        logger.error("Missing arguments. Required 5 given {}".format(len(sys.argv)))
        sys.exit(2)

    demand_queue = sys.argv[1]
    supply_queue = sys.argv[2]
    run_freq = int(sys.argv[3])
    agg_interval = int(sys.argv[4])
    max_surge = int(sys.argv[5])
    while True:
        now = datetime.now()

        logger.info("Fetching demand records...")
        geo_demand = fetchRecords(demand_queue,now,agg_interval)
        logger.info("Total {} demand records fetched for {} geo_areas".format(sum(geo_demand.values()),len(geo_demand)))

        logger.info("Fetching supply records...")
        geo_supply = fetchRecords(supply_queue,now,agg_interval)
        logger.info("Total {} supply records fetched for {} geo_areas".format(sum(geo_supply.values()),len(geo_supply)))

        logger.info("Calculating surge for the areas...")
        geo_surge = compute_surge(geo_demand,geo_supply,max_surge)

        update_surge_table(geo_surge)
        time.sleep(60)
