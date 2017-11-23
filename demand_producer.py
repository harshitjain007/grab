import sys,time
import geohash
import json,csv
import boto3
from decimal import *

booking_request_queue = "request_queue"
kinesis_client = boto3.client("kinesis")

def write_to_kinesis(records):
    resp = kinesis_client.put_records(Records=records,StreamName=booking_request_queue)

if __name__ == "__main__":
    # if len(sys.argv) != 1:
    #     print "\n Frequency parameter missing \n eg. $ python demand_producer.py 10 \n"
    #     sys.exit(2)

    skip_header = True
    in_csv = '/Users/harshit/Documents/brag/data/tmp.csv'
    with open(in_csv, "rbU") as f:
        reader = csv.reader(f)
        if skip_header: next(reader, None)

        rows=1
        rec_list=[]
        hash_tab = {}
        for row in reader:
            hash_value = geohash.encode(Decimal(row[5]),Decimal(row[6]),6)
            rec = {"hash":hash_value,"lat":row[5],"long":row[6],"user_type":"rider"}
            rec_list.append(rec)
            rows = rows+1

            if rows%100==0:
                write_to_kinesis(rec_list)
                rec_list = []
                time.sleep(2)
