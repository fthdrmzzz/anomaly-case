
#%%
import time

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

#init
token = "l0km4GkohJyGjCdh4ORWuTojXmUD7mBHGMKRaIbgYe80G6Yu6HztoaJwZTJvqCiSEzWZBrkAF7ybqiWPkyHCJA=="
org = "example_org"
bucket = "example_bucket"

client = InfluxDBClient(url="http://localhost:8086", token=token)

#%%
# write
write_api = client.write_api(write_options=SYNCHRONOUS)

while True:
    
    data = "mem,host=host1 used_percent=23.43234543"
    write_api.write(bucket, org, data)
    time.sleep(5)

# %%
