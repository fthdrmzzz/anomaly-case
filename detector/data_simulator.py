
#%%
import os
import time
from influxdb_client import InfluxDBClient, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
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

#heart rate
hr_summer_high = 100
hr_summer_low = 85

hr_winter_high = 20
hr_winter_low = 12

#daily activity minutes
dam_summer_high = 1000
dam_summer_low = 600

dam_winter_high = 30
dam_winter_low = 0


#write in loop
# write_api = client.write_api(write_options=SYNCHRONOUS)
# while True:
#     data = "mem,host=host1 used_percent=23.43234543"
#     write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, data)
#     time.sleep(5)

# %%
# First we'll simulate the synthetic data
def simulate_seasonal_term(periodicity, total_cycles, noise_std=1.,
                           harmonics=None):
    duration = periodicity * total_cycles
    assert duration == int(duration)
    duration = int(duration)
    harmonics = harmonics if harmonics else int(np.floor(periodicity / 2))

    lambda_p = 2 * np.pi / float(periodicity)

    gamma_jt = noise_std * np.random.randn((harmonics))
    gamma_star_jt = noise_std * np.random.randn((harmonics))

    total_timesteps = 100 * duration # Pad for burn in
    series = np.zeros(total_timesteps)
    for t in range(total_timesteps):
        gamma_jtp1 = np.zeros_like(gamma_jt)
        gamma_star_jtp1 = np.zeros_like(gamma_star_jt)
        for j in range(1, harmonics + 1):
            cos_j = np.cos(lambda_p * j)
            sin_j = np.sin(lambda_p * j)
            gamma_jtp1[j - 1] = (gamma_jt[j - 1] * cos_j
                                 + gamma_star_jt[j - 1] * sin_j
                                 + noise_std * np.random.randn())
            gamma_star_jtp1[j - 1] = (- gamma_jt[j - 1] * sin_j
                                      + gamma_star_jt[j - 1] * cos_j
                                      + noise_std * np.random.randn())
        series[t] = np.sum(gamma_jtp1)
        gamma_jt = gamma_jtp1
        gamma_star_jt = gamma_star_jtp1
    wanted_series = series[-duration:] # Discard burn in

    return wanted_series

#%%

duration = 100 * 3
periodicities = [10, 100]
num_harmonics = [3, 2]
std = np.array([2, 3])
np.random.seed(8678309)

terms = []
for ix, _ in enumerate(periodicities):
    s = simulate_seasonal_term(
        periodicities[ix],
        duration / periodicities[ix],
        harmonics=num_harmonics[ix],
        noise_std=std[ix])
    
    terms.append(s)
terms.append(np.ones_like(terms[0])) #* 10.)
series = pd.Series(np.sum(terms, axis=0))
df = pd.DataFrame(data={'total': series,
                        '10(3)': terms[0],
                        '100(2)': terms[1],
                        'level':terms[2]})
h1, = plt.plot(df['total'])
h2, = plt.plot(df['10(3)'])
h3, = plt.plot(df['100(2)'])
h4, = plt.plot(df['level'])
plt.legend(['total','10(3)','100(2)', 'level'])
plt.show()


#%%

