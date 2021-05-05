# IBF-ERA-mosquito-model
Predict mosquito abundance from meteorological data.

## Setup
Generic requirements:
-   [Google Cloud account](https://cloud.google.com/)
-   [Google Earth Engine service account](https://developers.google.com/earth-engine/guides/service_account)

For 510: Project service account accessible [here](https://console.cloud.google.com/iam-admin/serviceaccounts/details/109300242343650934727;edit=true?previousPage=%2Fapis%2Fcredentials%3Fauthuser%3D1%26project%3Depidemic-risk-assessment&authuser=1&folder=&organizationId=&project=epidemic-risk-assessment), login credentials in Bitwarden

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
Specific requirements:
-   [Python >= 3.6.5](https://www.python.org/downloads/)

1. Move to project root 
```
cd mosquito_model
```
2. Install project
```
pip install .
```
3. Download input data from [here](https://rodekruis.sharepoint.com/sites/510-CRAVK-510/_layouts/15/guestaccess.aspx?docid=01fe7b3505b0440229856228d6210044c&authkey=Acr_sCnyg7cKHmMUw0ay1C8&expiration=2022-03-21T23%3A00%3A00.000Z&e=ciWvIh) and move it to
```
mosquito_model/input/
```
5. Copy your Google Earth Engine service account credentials (stored as .json) in
```
mosquito_model/credentials/
```

## Usage
```
Usage: run-mosquito-model [OPTIONS]

Options:
  --countrycode TEXT             country iso code
  --vector TEXT                  vector file with admin boundaries
  --temperaturesuitability TEXT  table with suitability vs temperature
  --thresholds TEXT              table with thresholds and coefficients to convert risk to dengue cases
  --demographics TEXT            table with demographic data
  --credentials TEXT             directory with credentials
  --admincode TEXT               which feature in vector file
  --data TEXT                    input data directory
  --dest TEXT                    output data directory
  --predictstart TEXT            start predictions from date (%Y-%m-%d)
  --predictend TEXT              end predictions on date (%Y-%m-%d)
  --storeraster                  store raster data
  --verbose                      print each step
  --ibfupload                    upload output to IBF system
  --help                         Show this message and exit.
  ```
