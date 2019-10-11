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

## NPM
```
npm install
```

## Bower install:
```
node_modules/bower/bin/bower install
```

# Run app:
```
ENV_FOR_DYNACONF=production SETTINGS_FILE_FOR_DYNACONF='/path/to/config.yml python app.py
```
from the root directory(Not from web dir)

# Open app in browser:
```
http://localhost:4000
```
