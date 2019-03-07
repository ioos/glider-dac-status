# glider-dac-status

Status Application for Glider DAC

This repository contains the GliderDAC status page, NAVO harvesting, and code for generating profile images

Please do not file issues here,  all GliderDAC related issues should be filed in the [IOOS National Glider Data Assembly Center (V2)](OOS National Glider Data Assembly Center (V2)) repository.

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
python app.py
```
from the root directory(Not from web dir)

# Open app in browser:
```
http://localhost:4000
```