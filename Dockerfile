FROM node:13.0.1-alpine AS buildstep
LABEL maintainer "RPS <devops@rpsgroup.com>"

RUN mkdir -p /web
WORKDIR /web

COPY ./web/ /web/
RUN yarn global add grunt-cli && \
    yarn install && \
    grunt

FROM python:3.8
ARG glider_gid_uid=1000

RUN mkdir -p /glider-dac-status /mpl_config
RUN mkdir -p /tmp/mplconfig /tmp/.cache && chmod -R 777 /tmp/mplconfig /tmp/.cache

VOLUME /mpl_config
RUN mkdir /glider-dac-status/logs
COPY app.py config.yml flask_environments.py manage.py /glider-dac-status/
COPY status /glider-dac-status/status
COPY navo /glider-dac-status/navo
COPY requirements/requirements.txt /requirements.txt

WORKDIR /glider-dac-status

# 1. System dependencies

RUN apt-get update && \
    apt-get install -y \
        python3-dev \
        python3-netcdf4 \  
        libnetcdf-dev \
        libhdf5-dev \
        libproj-dev \
        proj-data \
        proj-bin \
        libgeos-dev \
        libgdal-dev \
        gdal-bin \
        libjpeg-dev \
        libpng-dev \
        libfreetype6-dev \
        pkg-config \
        build-essential && \
    rm -rf /var/lib/apt/lists/*

# 2. Upgrade pip/setuptools/wheel for compatibility with build tooling
RUN pip install --upgrade "pip<24.1" "setuptools<60" "wheel<0.45"

# 3. Numpy must be installed first
RUN pip install numpy==1.24.4

# 4. Avoid building pandas from source
RUN pip install --prefer-binary pandas

# 5. setuptools and Cython and gunicorn 
RUN pip install "setuptools<58"
RUN pip install --no-cache-dir 'Cython<3.0' gunicorn

# 6. Install project requirements
COPY requirements/requirements.txt /requirements.txt
RUN pip install --no-cache-dir --prefer-binary -r /requirements.txt

# 7. Create user
RUN groupadd -g $glider_gid_uid glider && \
    useradd -u $glider_gid_uid -g $glider_gid_uid glider


ENV FLASK_ENV="PRODUCTION"
COPY --from=buildstep /web/ /glider-dac-status/web
RUN chown -R glider:glider /glider-dac-status/ /mpl_config

# ...
RUN chown -R glider:glider /glider-dac-status/ /mpl_config

ENV CARTOPY_USER_BACKGROUNDS=/tmp/cartopy_data
ENV CARTOPY_USERDATA_DIR=/tmp/cartopy_data

USER glider
EXPOSE 5000
