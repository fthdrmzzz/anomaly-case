# How to run?

just run `make run` on working directory. Influxdb (timeseries database) will be running in a container, and will be exposed on port `8086`.


You can check if it is running by going `http://localhost:8086`. Username and password information is in `.env` file.

# How to add data?
influxdb provides ready to run code in its ui. I have copied it to `data_simulator.py`. So you can just run that python code. No need to run in docker.


After running it, it will add data every 5 seconds. You can observe it in the UI:

![alt text](docs/image.png)



# Thought process

We need to be evaluating anomalies wrt their surroundings. One point can be normal depending on its surroundings. The bear will be hunting, fighting with other bears. 


# Data to Collect
- Sample collected from `https://datadryad.org/stash/dataset/doi:10.5061/dryad.6tt0h5s`.


- [] Age of the bear.
- [] Max-min normal heartbeat in summer.
- [] Maxmin normal heartbeet in winter.
- [] heartbeat rates of an older bear -> To have a declining trend over years. (optional)