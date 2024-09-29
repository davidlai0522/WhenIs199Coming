#!/usr/bin/env python3
import time
from datetime import datetime, timedelta

def process_time(timestamp_str, include_date: bool = False):
    timestamp_dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
    if not include_date:
        return timestamp_dt.strftime("%H:%M:%S")
    else:
        return timestamp_dt
    
def datetime_to_timestamp(timestamp_str):
    timestamp_dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
    return timestamp_dt.timestamp()

def get_time_now():
    return datetime.now()

def get_datetime_now():
    return datetime.now()

def get_timestamp_now():
    return time.time()

def sec_to_min(sec):
    return sec/60.0

def min_to_sec(min):
    return min * 60.0