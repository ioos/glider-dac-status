[![Build Status](https://travis-ci.com/ioos/glider-dac-status.svg?branch=master)](https://travis-ci.com/ioos/glider-dac-status)

# glider-dac-status

Status Application for Glider DAC

This repository contains the GliderDAC status page, NAVO harvesting, and code for generating profile images

Please do not file issues here,  all GliderDAC related issues should be filed in the [IOOS National Glider Data Assembly Center (V2)](https://github.com/ioos/ioosngdac) repository.

# Setup
## Install requirements
pip install -r requirements/dev.txt

# Web app
## Move to the /web directory
```
cd web
```

## Yarn
```
yarn global add grunt-cli
yarn install
grunt
```

# Run app:
```
python app.py
```
from the root directory

# Open app in browser:
```
http://localhost:4000
```

# Run celery workers
```
celery worker -A app.celery --loglevel=info
```

# Run celery beat

This will kick off tasks at regular intervals.

Tasks include get_dac_profile_plots and get_dac_status
```
celery beat -A app.celery --loglevel=info

```

# Deploy
## Using docker-compose

Check out the docker-compose.yml file located at the root of this project
```
docker-compose up --build
```



