
#%%
import os
import time
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# TEMPORARY CONFIG
username_file = os.path.join('..', '.env.influxdb2-admin-username')
password_file = os.path.join('..', '.env.influxdb2-admin-password')
token_file = os.path.join('..', '.env.influxdb2-admin-token')

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read().strip()

INFLUXDB_USERNAME = read_file(username_file)
INFLUXDB_PASSWORD = read_file(password_file)
INFLUXDB_TOKEN = read_file(token_file)
INFLUXDB_ORG="example_org"
INFLUXDB_BUCKET="example_bucket"

client = InfluxDBClient(url="http://localhost:8086", token=INFLUXDB_TOKEN)


#%%
# WRITE IN LOOP
write_api = client.write_api(write_options=SYNCHRONOUS)

while True:
    
    data = "mem,host=host1 used_percent=23.43234543"
    write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, data)
    time.sleep(5)

# %%
