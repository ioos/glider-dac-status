FROM node:13.0.1-alpine AS buildstep
LABEL maintainer "RPS <devops@rpsgroup.com>"

RUN mkdir -p /web
WORKDIR /web

COPY ./web/ /web/
RUN yarn global add grunt-cli && \
    yarn install && \
    grunt

FROM python:3.6

RUN mkdir -p /glider-dac-status
RUN mkdir /glider-dac-status/logs
COPY app.py config.yml flask_environments.py manage.py /glider-dac-status/
COPY status /glider-dac-status/status
COPY navo /glider-dac-status/navo
COPY requirements/requirements.txt /requirements.txt
COPY tests/test_status.py /glider-dac-status/
RUN rm -f /glider-dac-status/test/test_status.py
COPY requirements/test_requirements.txt /test_requirements.txt

WORKDIR /glider-dac-status

RUN apt-get update && \
    apt-get install -y python3-netcdf4 && \
    pip install --no-cache cython gunicorn && \
    pip install --no-cache -r /requirements.txt && \
    pip install --no-cache -r /test_requirements.txt

COPY --from=buildstep /web/ /glider-dac-status/web
	
RUN pytest

