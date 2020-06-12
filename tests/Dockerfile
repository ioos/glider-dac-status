FROM python:3.6

LABEL maintainer "RPS <devops@rpsgroup.com>"

RUN mkdir -p /glider-dac-status
RUN mkdir /glider-dac-status/logs
COPY /web/ /glider-dac-status/web
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
    pip install --no-cache -r /test_requirements.txt && \
    rm -rf /var/lib/apt/lists/*

RUN pytest
