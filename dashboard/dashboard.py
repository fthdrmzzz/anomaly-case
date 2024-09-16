import pandas as pd
import panel as pn
import plotly.graph_objects as go
from influxdb_client import InfluxDBClient


pn.extension('plotly', 'tabulator', sizing_mode="stretch_both")

ACCENT = "teal"

styles = {
    "box-shadow": "rgba(50, 50, 93, 0.25) 0px 6px 12px -2px, rgba(0, 0, 0, 0.3) 0px 3px 7px -3px",
    "border-radius": "4px",
    "padding": "10px",
}



INFLUXDB_USERNAME = "admin"
INFLUXDB_PASSWORD = "password"
INFLUXDB_TOKEN = "G3UtSut5Kv-RuT32yh27StdDCrl4fu3uzxPLzdias8vFsNzyzgfw5kIX9iGvtLctAXpZjFItOUwA65YWtk_5fg=="
INFLUXDB_ORG = "example_org"
INFLUXDB_BUCKET = "example_bucket"
INFLUXDB_URL = "http://influxdb:8086"

client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
query_api = client.query_api()


flux_query_anomaly = f'''
from(bucket: "{INFLUXDB_BUCKET}")
    |> range(start: -1y)  
    |> filter(fn: (r) => r._measurement == "anomaly_data")
    |> filter(fn: (r) => r._field == "noisy" or r._field == "original_time" or r._field=="anomaly" or r._field=="loss" or r._field=="threshold")
    |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> keep(columns: ["noisy", "original_time","anomaly","loss","threshold"])
    |> sort(columns: ["original_time"])
'''


flux_query_heart_rate = '''
from(bucket: "example_bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "heart_rate")
  |> filter(fn: (r) => r._field == "smoothed" or r._field == "original_time")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> window(every: 2s) 
  |> map(fn: (r) => ({
      _time: time(v: r.original_time),  
      smoothed: r.smoothed
  }))
'''

flux_query_noisy = '''
from(bucket: "example_bucket")
  |> range(start: -15m)
  |> filter(fn: (r) => r._measurement == "heart_rate")
  |> filter(fn: (r) => r._field == "noisy" or r._field == "original_time")
  |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> filter(fn: (r) => exists r.noisy)
  |> window(every: 10h) 
  |> map(fn: (r) => ({
      _time: time(v: r.original_time),
      noisy: r.noisy
  }))
'''


df_noisy = query_api.query_data_frame(query=flux_query_noisy)
df_noisy.set_index('_time', inplace=True)
df_noisy.index = pd.to_datetime(df_noisy.index)
most_recent_date = df_noisy.index.max()
three_years_before = most_recent_date - pd.DateOffset(years=3)
df_noisy = df_noisy[df_noisy.index >= three_years_before]


df_heart_rate = query_api.query_data_frame(query=flux_query_heart_rate)
df_heart_rate.set_index('_time', inplace=True)
df_heart_rate.index = pd.to_datetime(df_heart_rate.index)
most_recent_date = df_heart_rate.index.max()
three_years_before = most_recent_date - pd.DateOffset(years=3)
df_heart_rate = df_heart_rate[df_heart_rate.index >= three_years_before]

df_anomaly = query_api.query_data_frame(query=flux_query_anomaly)
df_anomaly.set_index('original_time', inplace=True)
df_anomaly.index = pd.to_datetime(df_anomaly.index)
most_recent_date = df_anomaly.index.max()
three_years_before = most_recent_date - pd.DateOffset(years=3)
df_anomaly = df_anomaly[df_anomaly.index >= three_years_before]

anom_df = df_anomaly


def create_anomaly_plot():
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=anom_df.index, 
        y=anom_df['noisy'], 
        mode='lines', 
        name='Data', 
        line=dict(color='blue')
    ))

    anomalies = anom_df[anom_df['anomaly'] == True]
    fig.add_trace(go.Scatter(
        x=anomalies.index, 
        y=anomalies['noisy'], 
        mode='markers', 
        name='Anomaly', 
        marker=dict(color='red', size=8)
    ))

    fig.update_xaxes(
        dtick="M1", 
        tickformat="%Y-%m",
        tickangle=45
    )

    fig.update_layout(
        title='Time Series Plot with Anomalies',
        xaxis_title='Time',
        yaxis_title='Value',
        legend_title='Legend',
        xaxis_rangeslider_visible=False,
        height=600,
        width=1000
    )

    return fig


def create_heart_rate_plot():
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_heart_rate.index, 
        y=df_heart_rate['smoothed'], 
        mode='lines', 
        name='Heart Rate (Smoothed)', 
        line=dict(color='green')
    ))

    fig.update_layout(
        title='Source of Data Stream',
        xaxis_title='Time',
        yaxis_title='Heart Rate (Smoothed)',
        legend_title='Legend',
        xaxis_rangeslider_visible=False,
        height=600,
        width=1000
    )

    return fig
def create_noisy_plot():
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_noisy.index, 
        y=df_noisy['noisy'], 
        mode='lines', 
        name='Noisy Data (Last 15 Minutes)', 
        line=dict(color='green')
    ))

    fig.update_layout(
        title='Heart Rate Over Time',
        xaxis_title='Time',
        yaxis_title='Noisy Value',
        legend_title='Legend',
        xaxis_rangeslider_visible=False,
        height=600,
        width=1000
    )

    return fig

anomaly_plot = pn.pane.Plotly(create_anomaly_plot(), sizing_mode="stretch_both", name="Anomaly Plot")
heart_rate_plot = pn.pane.Plotly(create_heart_rate_plot(), sizing_mode="stretch_both", name="Heart Rate Plot")
noisy_plot = pn.pane.Plotly(create_noisy_plot(), sizing_mode="stretch_both", name="Noisy Plot")


anomaly_table = pn.widgets.Tabulator(anom_df, sizing_mode="stretch_both", name="Anomaly Data")
heart_rate_table = pn.widgets.Tabulator(df_heart_rate, sizing_mode="stretch_both", name="Heart Rate Data")
noisy_table = pn.widgets.Tabulator(df_noisy, sizing_mode="stretch_both", name="Noisy Data")


anomaly_row = pn.Tabs(
    ("Anomaly Plot", anomaly_plot),
    ("Anomaly Data", anomaly_table),
    sizing_mode="stretch_width", height=500, margin=10
)

heart_rate_row = pn.Tabs(
    ("Heart Rate Plot", heart_rate_plot),
    ("Heart Rate Data", heart_rate_table),
    sizing_mode="stretch_width", height=500, margin=10
)

noisy_row = pn.Tabs(
    ("Noisy Plot", noisy_plot),
    ("Noisy Data", noisy_table),
    sizing_mode="stretch_width", height=500, margin=10
)


dashboard = pn.Column(
    
    heart_rate_row,
    pn.Spacer(height=120),  
    noisy_row,
    pn.Spacer(height=120), 
    anomaly_row,
    sizing_mode="stretch_both"
)


pn.template.FastListTemplate(
    title="Time Series Anomaly Detection Dashboard",
    sidebar=[],
    main=[dashboard],
    main_layout=None,
    accent=ACCENT,
).servable()