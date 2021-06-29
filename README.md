# IBF-dengue-mosquito-model

Forecast dengue outbreaks. Part of 510's [impact-based forecasting portal](https://www.510.global/impact-based-forecasting-system/). Built to support Philippines Red Cross.

This model:
1. calculates expected mosquito abundance given meteorological data
2. forecast dengue risk given mosquito abundance
3. determines if dengue risk is anomalously high and, if so, gives an *alert*
4. calculates the expected number of dengue cases given dengue risk

See details in the [IBF-dengue mosquito-model technical note](https://drive.google.com/file/d/1kCaJE2it05yPCkqzDGYd8cWjpTm53Nyd/view?usp=sharing).

## Setup
Generic requirements:
-   [Google Cloud account](https://cloud.google.com/)
-   [Google Earth Engine service account](https://developers.google.com/earth-engine/guides/service_account)

For 510: project service account accessible [here](https://console.cloud.google.com/iam-admin/serviceaccounts/details/109300242343650934727;edit=true?previousPage=%2Fapis%2Fcredentials%3Fauthuser%3D1%26project%3Depidemic-risk-assessment&authuser=1&folder=&organizationId=&project=epidemic-risk-assessment), login credentials in Bitwarden

### with Docker
1. Install [Docker](https://www.docker.com/get-started)
3. Download input data from [here](https://rodekruis.sharepoint.com/sites/510-CRAVK-510/_layouts/15/guestaccess.aspx?docid=01fe7b3505b0440229856228d6210044c&authkey=Acr_sCnyg7cKHmMUw0ay1C8&expiration=2022-03-21T23%3A00%3A00.000Z&e=ciWvIh) and move it to
```
mosquito_model/input/
```
5. Copy your Google Earth Engine service account credentials (stored as .json) and [IBF-system](https://github.com/rodekruis/IBF-system) credentials (stored as .env) in
```
mosquito_model/credentials/
```
3. Build the docker image from the root directory
```
docker build -t rodekruis/mosquito-model .
```
3. Create a docker container
```
docker run --name mosquito-model rodekruis/mosquito-model
```
4. Run and access the container
```
docker run -it --entrypoint /bin/bash rodekruis/mosquito-model
```
5. Check that everything is working by running the model (see [Usage](https://github.com/rodekruis/IBF-dengue-model#usage) below)


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
5. Copy your Google Earth Engine service account credentials (stored as .json) and [IBF-system](https://github.com/rodekruis/IBF-system) credentials (stored as .env) in
```
mosquito_model/credentials/
```


## Usage
```
Usage: run-mosquito-model [OPTIONS]

Options:
  --countrycode TEXT             country iso code
  --vector TEXT                  vector file with admin boundaries
  --admincode TEXT               name of admin code in vector file
  --temperaturesuitability TEXT  table with suitability vs temperature
  --thresholds TEXT              table with thresholds and coefficients (risk vs dengue cases)
  --demographics TEXT            table with demographic data
  --credentials TEXT             credentials directory
  --data TEXT                    input data directory
  --dest TEXT                    output data directory
  --predictstart TEXT            start predictions from date (%Y-%m-%d)
  --predictend TEXT              end predictions on date (%Y-%m-%d)
  --storeraster                  store raster data locally
  --verbose                      print output at each step
  --ibfupload                    upload to IBF-system via API
  --help                         show this message and exit
  ```
