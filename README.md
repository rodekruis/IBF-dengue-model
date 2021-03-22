# IBF-ERA-mosquito-model
Predict mosquito abundance from meteorological data.

## Setup
Requirements:
-   [Google Cloud account](https://cloud.google.com/)
-   [Google Earth Engine service account](https://developers.google.com/earth-engine/guides/service_account)

### with Docker

1. Install [Docker](https://www.docker.com/get-started)
2. Download the [mosquito-model docker image](https://hub.docker.com/r/rodekruis/mosquito-model)
```
docker pull rodekruis/mosquito-model
```
3. Create a docker container
```
docker run --name mosquito-model rodekruis/mosquito-model
```
4 Access the container
```
docker exec -it mosquito-model bash
```
5. Copy your Google Earth Engine service account credentials (stored as .json) in
```
mosquito_model/credentials/
```

### Manual Setup
Requirements:
-   [Python >= 3.6.5](https://www.python.org/downloads/)

1. Move to project root 
```
cd mosquito_model
```
2. Install project
```
pip install .
```
3. Copy your Google Earth Engine service account credentials (stored as .json) in
```
mosquito_model/credentials/
```

## Usage
```
Usage: run-mosquito-model [OPTIONS]

Options:
  --countrycode TEXT             country code (ISO 3166-1 alpha-3)
  --vector TEXT                  vector file with admin boundaries
  --temperaturesuitability TEXT  table with suitability vs temperature
  --geecredentials TEXT          Google Earth Engine credentials
  --admincode TEXT               which feature to use in vector file with admin boundaries
  --data TEXT                    input data directory
  --dest TEXT                    output data directory
  --predictstart TEXT            start predictions from date (%Y-%m-%d)
  --predictend TEXT              end predictions on date (%Y-%m-%d)
  --storeraster                  store raster data
  --help                         show this message and exit
  ```
