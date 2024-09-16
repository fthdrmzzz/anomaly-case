
import os
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime, timedelta, timezone

def read_secret(secret_name):
    secret_path = os.getenv(secret_name)
    try:
        with open(secret_path, 'r') as file:
            return file.read().strip()
    except Exception as e:
        print(f"Error reading {secret_name}: {e}")
        return None

INFLUXDB_USERNAME = read_secret('DOCKER_INFLUXDB_INIT_USERNAME_FILE')
INFLUXDB_PASSWORD = read_secret('DOCKER_INFLUXDB_INIT_PASSWORD_FILE')
INFLUXDB_TOKEN = read_secret('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN_FILE')

INFLUXDB_ORG = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
INFLUXDB_BUCKET = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
INFLUXDB_URL = os.getenv('INFLUXDB_URL', 'http://influxdb:8086') 



def convert_to_rfc3339(timestamp):
    if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    rfc3339_format = timestamp.isoformat()
    
    return rfc3339_format

class DayGenerator:
    def __init__(self, years_to_extend=1, noise_std=2.7, anomaly_prob=0.010):
        self.noise_std = noise_std

        self.df_original = pd.read_csv('./df_filtered_extended_final.csv')
        self.df_original['GMT_date'] = pd.to_datetime(self.df_original['GMT_date'])
        self.df_original['HeartRate_Smoothed'] = self.df_original['HeartRate'].rolling(window=10).mean()
        self.df_original['HeartRate_Noisy'] = self.df_original['HeartRate_Smoothed'] + np.random.normal(loc=0, scale=self.noise_std / 2, size=len(self.df_original))
        
        
        self.current_index = len(self.df_original)  
        self.years_to_extend = years_to_extend  
        self.df_extended = self.extend_df(self.df_original, years=years_to_extend)  
        self.anomaly_prob = anomaly_prob
    def extend_df(self, df, years=1):
        df = df.drop(columns=['Object_ID', 'Species'], errors='ignore')  
        df2 = df.copy()  
        df2['GMT_date'] = df2['GMT_date'] + pd.DateOffset(years=years)  
        
        df2['HeartRate_Noisy'] = df2['HeartRate_Smoothed'] + np.random.normal(loc=0, scale=self.noise_std / 2, size=len(df2))
        
        df_extended = pd.concat([df, df2], ignore_index=True)
        df_extended.set_index('GMT_date', inplace=True)
        df_extended = df_extended.resample('D').mean().interpolate(method='linear') 
        df_extended.reset_index(inplace=True)
        return df_extended
    def get_next_day(self, noise=True):
        results = []
        if self.current_index >= len(self.df_extended):
            self.df_extended = self.extend_df(self.df_extended, years=self.years_to_extend)

        base_data = self.df_extended.iloc[self.current_index]
        self.current_index += 1  

        for hour in [0,6,12,18]:
            modified_data = base_data.copy()
            modified_time = pd.Timestamp(modified_data['GMT_date']).replace(hour=hour, minute=0, second=0)
            modified_data['GMT_date'] = modified_time
            modified_data['HeartRate_Noisy'] += np.random.normal(loc=0, scale=self.noise_std / 10)

            if noise:
                if np.random.rand() < self.anomaly_prob:
                    anomaly_change = np.random.uniform(low=0.5, high=2) * modified_data['HeartRate_Noisy']
                    if np.random.rand() < 1/3:
                        modified_data['HeartRate_Noisy'] = max(modified_data['HeartRate_Noisy'] / 2, modified_data['HeartRate_Noisy'] - anomaly_change)
                    else:
                        modified_data['HeartRate_Noisy'] = max(modified_data['HeartRate_Noisy'] / 2, modified_data['HeartRate_Noisy'] + anomaly_change)

            
            results.append(modified_data)
        return results

    
if __name__ == '__main__':
    client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN)
    while True:
        try:
            if client.ping():
                print("Connected to InfluxDB successfully!")
                break
            else:
                print("InfluxDB server is up but not responding as expected.")
        except Exception as e:
            print(f"Failed to connect to InfluxDB: {e}")

        print("Retrying in 5 seconds...")
        time.sleep(5)
    day_gen = DayGenerator(years_to_extend=1)
    write_api = client.write_api(write_options=SYNCHRONOUS)
    try:
        time_added = datetime.utcnow() - timedelta(seconds=365)
        time.sleep(0.25)
        for i in range(0,365):
            day_data_points = day_gen.get_next_day(noise=False)
            for data_point in day_data_points:
                print(data_point)

                influx_data_point = Point("heart_rate") \
                    .tag("unit", "bpm") \
                    .field("smoothed", data_point['HeartRate_Smoothed']) \
                    .field("noisy", data_point['HeartRate_Noisy']) \
                    .field("original_time", convert_to_rfc3339(data_point['GMT_date'])) \
                    .time(datetime.utcnow(), WritePrecision.MS)

                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=influx_data_point)
        
        while True:
            day_data_points = day_gen.get_next_day()
            ctr = 0
            for data_point in day_data_points:
                ctr+=1
                if ctr%1000==0:
                    print(data_point)

                influx_data_point = Point("heart_rate") \
                    .tag("unit", "bpm") \
                    .field("smoothed", data_point['HeartRate_Smoothed']) \
                    .field("noisy", data_point['HeartRate_Noisy']) \
                    .field("original_time", convert_to_rfc3339(data_point['GMT_date'])) \
                    .time(datetime.utcnow(), WritePrecision.MS)

                write_api.write(bucket=INFLUXDB_BUCKET, org=INFLUXDB_ORG, record=influx_data_point)
                time.sleep(0.03)

    except KeyboardInterrupt:
        print("Interrupted, shutting down.")
        write_api.close()
        client.close()
