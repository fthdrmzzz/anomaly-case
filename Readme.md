___

- [Anomaly Detection Case](#anomaly-detection-case)
  - [Requirements](#requirements)
  - [Show Me the Demo](#show-me-the-demo)
  - [Data Simulation](#data-simulation)
    - [What Is Our Data?](#what-is-our-data)
    - [Generating the Data](#generating-the-data)
  - [Anomaly Detection](#anomaly-detection)
  - [Implementation and Used Technologies](#implementation-and-used-technologies)
___

# Anomaly Detection Case
## Requirements
- git
- docker
- docker-compose
- make
## Show Me the Demo

1. **Clone the Repository:**
   ```bash
   git clone <link>
   ```

2. **Navigate to the Working Directory:**
   ```bash
   cd anomaly_case
   ```

3. **Run the Project:**
   ```bash
   make run
   ```
   This will start containers for data population and anomaly detection. The dashboard will be available at `http://localhost:5006/dashboard`. It may take up to 5 minutes to display detected anomalies. To see changes in data **refresh** the page.

## Data Simulation

### What Is Our Data?

I aimed to work with a different dataset than classical seasonal data like Wi-Fi sessions or yearly sales. I chose bear activity data due to their hibernation patterns, which could reveal interesting insights.

I discovered a [research article](https://www.nature.com/articles/srep40732) on the effects of human interaction on bears' stress levels and used it as inspiration. My virtual motivation was to create data to detect sudden changes in an endangered animal's activity and alert authorities for protection.

![Bear Activity](image.png)

### Generating the Data

I found an incomplete [yearly hibernation dataset](https://datadryad.org/stash/dataset/doi:10.5061/dryad.6tt0h5s). To complete it, I extended the data by following the trend of initial hibernation. I added white noise to maintain the original entropy and generated the remaining data. The generated data is shown in green.

![Generated Data](image-1.png)

After generating the data for one season, I smoothed it using a windowed mean. I added white noise for natural deviations and occasional large values to simulate anomalies. An example of the data stream is shown below. 

![Data Stream](image-3.png)

## Anomaly Detection

I have decided to go with auto-encoding to implement anomaly detection in this project. In simple terms, our model tries to reconstruct the data we provided in training. And the loss is how far is newly introduced data from the guess of our model. If loss is larger than a certain threshold (setup manually since we only have non-anomaly data for training) the data point that is responsible for that loss is flagged as anomaly. Below you can see effectiveness of loss-threshold model in detecting introduced anomalies. First graph shows the loss vs threshold  during time. The second graph shows, introduced anomalies in generated data.

![alt text](image-4.png)

## Implementation and Used Technologies
```
C:.
│   .env
│   docker-compose.yml
│   Makefile
│   Readme.md
├───dashboard
│       dashboard.py
│       Dockerfile
│       requirements.txt
├───data_sim
│       data_simulator.py
│       df_filtered_extended_final.csv
│       Dockerfile
│       requirements.txt
├───detector
│       anomaly_detection.py
│       Dockerfile
│       requirements.txt
├───influxdb
│       Dockerfile
│       stream.json
└───preprocessing
        ad_from_experimentdata.ipynb
        anomaly_detection.ipynb
        data_gen.ipynb
        preprocess.ipynb
```
I aimed to prepare the project to be ready to run on any system that can run docker. The file hierarchy can be seen above. `data_sim` simulates the data stream and pushes the data to the timeseries database. 

`influxdb` is the timeseries database used to push and read data. `data_sim` and `detector` pushes to `influxdb`, `dashboard` and `detector` reads from influxdb. 

`detector` is the program where anomaly detection is done. It pulls first year of data from influxdb. Then trains the autoencoder lstm model with first years data. Then, it starts testing the stream data constantly being pushed by `data_sim`. Data flagged by `detector` is later pushed to `influxdb`.

`dashboard`, pulls stream data and anomaly flagged data from `influxdb` and exports the dashboard.

`Preprocessing` folder was used as playground.