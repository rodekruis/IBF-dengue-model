# IBF-dengue-mosquito-model

Forecast dengue outbreaks. Part of 510's [impact-based forecasting portal](https://www.510.global/impact-based-forecasting-system/). Built to support Philippines Red Cross.

This model:
1. calculates expected mosquito abundance given meteorological data
2. forecast dengue risk given mosquito abundance
3. determines if dengue risk is anomalously high and, if so, gives an *alert*
4. calculates the expected number of dengue cases given dengue risk

See details in the [IBF-dengue technical note](https://drive.google.com/file/d/1kCaJE2it05yPCkqzDGYd8cWjpTm53Nyd/view?usp=sharing).

**If you want to run this model on [Azure](https://en.wikipedia.org/wiki/Microsoft_Azure), follow [these instructions](https://docs.google.com/document/d/182aQPVRZkXifHDNjmE66tj5L1l4IvAt99rxBzpmISPU/edit?usp=sharing)**.

## Setup
Generic requirements:
-   [Google Cloud account](https://cloud.google.com/)
-   [Google Earth Engine service account](https://developers.google.com/earth-engine/guides/service_account)

For 510: project service account accessible [here](https://console.cloud.google.com/iam-admin/serviceaccounts/details/109300242343650934727;edit=true?previousPage=%2Fapis%2Fcredentials%3Fauthuser%3D1%26project%3Depidemic-risk-assessment&authuser=1&folder=&organizationId=&project=epidemic-risk-assessment), login credentials in Bitwarden

### with Docker
1. Install [Docker](https://www.docker.com/get-started)
3. Download input data from [here](https://drive.google.com/file/d/1O_x3oUdgdUPAGPymJGpu1ggAI5YRUTpR/view?usp=sharing) and move it to
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
3. Download input data from [here](https://drive.google.com/file/d/1O_x3oUdgdUPAGPymJGpu1ggAI5YRUTpR/view?usp=sharing) and move it to
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
  --help                         show this message and exit
  ```
