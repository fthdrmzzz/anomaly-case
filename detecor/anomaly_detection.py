




#%%


# def read_secret(secret_name):
#     secret_path = os.getenv(secret_name)
#     try:
#         with open(secret_path, 'r') as file:
#             return file.read().strip()
#     except Exception as e:
#         print(f"Error reading {secret_name}: {e}")
#         return None

# INFLUXDB_USERNAME = read_secret('DOCKER_INFLUXDB_INIT_USERNAME_FILE')
# INFLUXDB_PASSWORD = read_secret('DOCKER_INFLUXDB_INIT_PASSWORD_FILE')
# INFLUXDB_TOKEN = read_secret('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN_FILE')

# INFLUXDB_ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
# INFLUXDB_BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
# INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086') 
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.query_api import QueryOptions
import pandas as pd
import os
INFLUXDB_USERNAME="admin"
INFLUXDB_PASSWORD="password"
INFLUXDB_TOKEN="G3UtSut5Kv-RuT32yh27StdDCrl4fu3uzxPLzdias8vFsNzyzgfw5kIX9iGvtLctAXpZjFItOUwA65YWtk_5fg=="
INFLUXDB_ORG="example_org"
INFLUXDB_BUCKET="example_bucket"
INFLUXDB_URL="http://localhost:8086"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)

# Create a QueryAPI instance
query_api = client.query_api(query_options=QueryOptions(profilers=["query", "operator"]))


#%%
# Flux query
query = f'''
from(bucket: "{INFLUXDB_BUCKET}")
        |> range(start: -5h)
        |> filter(fn: (r) => r._measurement == "heart_rate")
        |> filter(fn: (r) => r._field == "noisy" or r._field == "original_time")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        |> keep(columns: ["noisy", "original_time"])
'''

# Execute the query
result = query_api.query_data_frame(query=query)

# Closing the client
client.close()

result.drop(columns=['table','_result'],inplace=True)


#%%

print(result.head())
# %%
