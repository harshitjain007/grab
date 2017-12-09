import sys,time
import geohash
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
