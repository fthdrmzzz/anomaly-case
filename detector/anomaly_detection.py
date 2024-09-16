


from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.client.query_api import QueryOptions
import pandas as pd
import numpy as np
import os
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Dropout, RepeatVector, TimeDistributed
from datetime import datetime, timedelta, timezone
import plotly.graph_objects as go
import time
import pytz


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






class AnomalyDetector():
    def __init__(self,url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG,bucket=INFLUXDB_BUCKET):
        self.url = url
        self.token=token
        self.org = org
        self.bucket=bucket
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.query_api = self.client.query_api(query_options=QueryOptions(profilers=[]))
        
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.training_df = pd.DataFrame()
        self.bucket=bucket
        self.last_pull_time = datetime.now()
        
        self.model = None
        self.scaler = None
        self.time_steps=30
        self.current_year=2017
    def run(self):
        
        while True:
            current_year = self.current_year
            start_time = f"{current_year}-05-10T00:00:00Z"
            stop_time = f"{current_year + 1}-05-10T00:00:00Z"

            flux_query = f'''
            from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: -1y)  
                |> filter(fn: (r) => r._measurement == "heart_rate")
                |> filter(fn: (r) => r._field == "noisy" or r._field == "original_time")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> filter(fn: (r) => time(v: r.original_time)>= time(v: "{start_time}") and time(v: r.original_time) < time(v: "{stop_time}"))
                |> keep(columns: ["noisy", "original_time"])
                |> sort(columns: ["original_time"])
            '''
            new_df = self.query_api.query_data_frame(query=flux_query)
            if len(new_df)<363*4:
                time.sleep(5)
                continue
            
            self.current_year+=1
            
            new_df.set_index('original_time',inplace=True)
            new_df.index = pd.to_datetime(new_df.index)
      
            anomaly_flagged_df = self.detect_anomalies(new_df)
            self.push_data_to_influxdb(anomaly_flagged_df)

    def push_data_to_influxdb(self,df):
        
        points = []
        for idx, row in df.iterrows():
            points.append(
                Point("anomaly_data")
                .tag("unit", "bpm")
                .field("noisy", row['noisy'])
                .field("anomaly", row['anomaly'])
                .field("loss", row['loss'])
                .field("threshold", row['threshold'])
                .field("original_time", idx.isoformat())  
                .time(datetime.utcnow(),WritePrecision.NS)  
            )
        self.write_api.write(bucket=self.bucket, record=points)
            
    def has_one_year(self, df):
        time_span = df.index.max() - df.index.min()
        return time_span >= pd.Timedelta(days=365)
    

    def create_dataset(self, X, y, time_steps=1):
            Xs, ys = [], []
            for i in range(len(X) - time_steps):
                v = X.iloc[i:(i + time_steps)].values
                Xs.append(v)        
                ys.append(y.iloc[i + time_steps])
            return np.array(Xs), np.array(ys)
        
    def train_model(self):
        train_data = self.training_df

        scaler = StandardScaler()
        scaler = scaler.fit(train_data[['noisy']])
        self.scaler = scaler
        train_data['noisy_scl'] = scaler.transform(train_data[['noisy']])
        train_data.head()

        

        time_steps = self.time_steps
        X_train, y_train = self.create_dataset(train_data[['noisy_scl']], train_data.noisy_scl, time_steps)

        num_features=1
        model = Sequential([
            LSTM(128, input_shape=(time_steps, num_features)),
            Dropout(0.2),
            RepeatVector(time_steps),
            LSTM(128, return_sequences=True),
            Dropout(0.2),
            TimeDistributed(Dense(num_features))                 
        ])

        model.compile(loss='mae', optimizer='adam')
        history = model.fit(
            X_train, y_train,
            epochs=30,
            batch_size=32,
            validation_split=0.1,
            shuffle=False,
        )
        
        self.model = model
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=train_data.index, y=train_data.noisy,
                            mode='lines',
                            name='rate'))
        fig.update_layout(showlegend=True)
        fig.show()         
            
    def detect_anomalies(self, new_df):
        test_data = new_df.copy()
        model = self.model
        time_steps = self.time_steps
        test_data['noisy_scl'] = self.scaler.transform(test_data[['noisy']])
        X_test, y_test = self.create_dataset(test_data[['noisy_scl']], test_data.noisy_scl, time_steps)
        X_test_pred = model.predict(X_test)
        test_mae_loss = np.mean(np.abs(X_test_pred - X_test), axis=1)

        THRESHOLD = 0.48

        test_score_df = pd.DataFrame(test_data[time_steps:])
        test_score_df['loss'] = test_mae_loss
        test_score_df['threshold'] = THRESHOLD
        test_score_df['anomaly'] = test_score_df.loss > test_score_df.threshold
        test_score_df['noisy'] = test_data[time_steps:].noisy
        
        test_score_df['date'] = test_score_df.index.date
        test_score_df['date'] = pd.to_datetime(test_score_df['date']).dt.date
        anomalous_dates = test_score_df[test_score_df['anomaly']]['date'].unique()

        anomalous_dates = pd.Series(anomalous_dates)
        extended_anomalous_dates = pd.concat([anomalous_dates,
                                            anomalous_dates - pd.Timedelta(days=1),
                                            anomalous_dates + pd.Timedelta(days=1)])
        extended_anomalous_dates = extended_anomalous_dates.unique()
        test_score_df['anomaly'] = test_score_df['date'].isin(extended_anomalous_dates)
        test_score_df.drop(columns='date', inplace=True) 


        return test_score_df

    def get_dataframe_starting(self, starting_time):
        print("Pulling new data starting: ",starting_time)
        query = f'''
        from(bucket: "{INFLUXDB_BUCKET}")
                |> range(start: {starting_time})
                |> filter(fn: (r) => r._measurement == "heart_rate")
                |> filter(fn: (r) => r._field == "noisy" or r._field == "original_time")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> keep(columns: ["noisy", "original_time"])
        '''
        print(query)
        df = self.query_api.query_data_frame(query=query)
        if not df.empty:
            self.last_pull_time = (datetime.utcnow().replace(tzinfo=pytz.utc) -timedelta(seconds=60)).isoformat()
            df.drop(columns=['table','result'],inplace=True)
            df['original_time'] = pd.to_datetime(df['original_time'])
        return  df
    
    def get_dataframe_initial(self):
        checkpoint_df = self.get_dataframe_starting('-24h')
        earliest_time = checkpoint_df['original_time'].min()
        one_year_after_earliest = earliest_time + pd.DateOffset(years=1)
        training_df = checkpoint_df[checkpoint_df['original_time'] <= one_year_after_earliest]
        training_df['anomaly'] = False
        training_df.set_index('original_time',inplace=True)
        training_df.index = pd.to_datetime(training_df.index)

        print('Length of training dataframe',len(training_df))
        while len(training_df)<363*4:
            checkpoint_df = self.get_dataframe_starting('-24h')
            earliest_time = checkpoint_df['original_time'].min()
            one_year_after_earliest = earliest_time + pd.DateOffset(years=1)
            training_df = checkpoint_df[checkpoint_df['original_time'] <= one_year_after_earliest]
            training_df['anomaly'] = False
            training_df.set_index('original_time',inplace=True)
            training_df.index = pd.to_datetime(training_df.index)
            time.sleep(3)

        self.training_df = training_df

if __name__ == '__main__':
        try:
                ad = AnomalyDetector(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG, bucket=INFLUXDB_BUCKET)
                ad.get_dataframe_initial()
                ad.train_model()
                ad.run()
        except KeyboardInterrupt:
                print("Interrupted by user, closing client.")
                ad.close()