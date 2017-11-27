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
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def writeToQueue(queue_name,records):
    resp = kinesis_client.put_records(Records=records,StreamName=queue_name)
    shards = Set([])
    for rec in resp["Records"]: shards.add(rec["ShardId"])

    fail_cnt = resp['FailedRecordCount']
    success_cnt = len(records) - fail_cnt

    logger.info('SucessWrites:{}  FailedWrites:{} Shards:{}'.format(success_cnt,fail_cnt,str(list(shards))))

if __name__ == "__main__":
    total_params = 3
    params_given = len(sys.argv)
    if params_given != total_params+1:
        logger.error("Missing arguments. Required {} given {}".format(total_params,params_given))
        sys.exit(2)

    skip_header = True
    in_csv = sys.argv[1]
    queue_name = sys.argv[2]
    write_freq = int(sys.argv[3])

    with open(in_csv, "rbU") as f:
        reader = csv.reader(f)
        if skip_header: next(reader, None)

        rows=1
        rec_list=[]
        for row in reader:
            hash_value = geohash.encode(Decimal(row[5]), Decimal(row[6]), 6)
            pay_load = {"hash":hash_value,"lat":row[5],"long":row[6],"ts":datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            rec_list.append({
                'Data': json.dumps(pay_load),
                'PartitionKey':'p1'
            })
            rows = rows+1

            if rows%100==0:
                writeToQueue(queue_name,rec_list)
                rec_list = []
                time.sleep(write_freq)

