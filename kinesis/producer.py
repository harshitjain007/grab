import sys,time
import geohash
import json,csv
import boto3
import logging
from decimal import *
from datetime import datetime
from sets import Set

kinesis_client = boto3.client("kinesis")

#logging
logger = None

def writeToQueue(queue_name,records):
    resp = kinesis_client.put_records(Records=records,StreamName=queue_name)
    shards = Set([])
    try:
        for rec in resp["Records"]: shards.add(rec["ShardId"])

        fail_cnt = resp['FailedRecordCount']
        success_cnt = len(records) - fail_cnt

        logger.info('SucessWrites:{}  FailedWrites:{} Shards:{}'.format(success_cnt,fail_cnt,str(list(shards))))
    except Exception as e:
        print(resp)
        print(e)

if __name__ == "__main__":
    total_params = 4
    params_given = len(sys.argv)
    if params_given-1 != total_params:
        print("Missing arguments. Required {} given {}".format(total_params,params_given-1))
        sys.exit(2)

    skip_header = True
    in_csv = sys.argv[1]
    queue_name = sys.argv[2]
    sleep_time = float(sys.argv[3])
    log_file = sys.argv[4]

    logging.basicConfig(filename=log_file,format='%(asctime)s - %(levelname)s - %(message)s',level=logging.INFO)
    logger=logging.getLogger(__name__)

    with open(in_csv, "rbU") as f:
        reader = csv.reader(f)
        if skip_header: next(reader, None)

        rows=1
        rec_list=[]
        for row in reader:
            hash_value = geohash.encode(Decimal(row[6]), Decimal(row[5]), 6)
            pay_load = {"hash":hash_value,"lat":row[6],"long":row[5],"ts":datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            rec_list.append({
                'Data': json.dumps(pay_load),
                'PartitionKey':'p1'
            })
            rows = rows+1

            writeToQueue(queue_name,rec_list)
            rec_list = []
            time.sleep(sleep_time)
