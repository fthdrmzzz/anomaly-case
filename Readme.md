# How to run?

just run `make run` on working directory. Influxdb (timeseries database) will be running in a container, and will be exposed on port `8086`.


You can check if it is running by going `http://localhost:8086`. Username and password information is in `.env` file.

# How to add data?
The data_sim docker container will be adding data already. You can view added data in influxdb dashboard. 
- Open the `http://localhost:8086`.
- Login using username and password.
- Then, go to dashboards.
- Click create new dashboard -> import from json
- copy ./influxdb/stream.json there.
- then open dashboard named stream. You can see the data stream




# Anomaly Detection

anomaly_detection.ipynb under development right now.

# Data to Collect
- Sample collected from `https://datadryad.org/stash/dataset/doi:10.5061/dryad.6tt0h5s`.


- [] Age of the bear.
- [] Max-min normal heartbeat in summer.
- [] Maxmin normal heartbeet in winter.
- [] heartbeat rates of an older bear -> To have a declining trend over years. (optional)
