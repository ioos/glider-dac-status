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

WORKDIR /glider-dac-status

RUN apt-get update && \
    apt-get install -y python3-netcdf4 && \
    pip install --no-cache cython gunicorn && \
    pip install --no-cache -r /requirements.txt && \
    rm -rf /var/lib/apt/lists/* && \
    useradd glider


ENV FLASK_ENV="PRODUCTION"
COPY --from=buildstep /web/ /glider-dac-status/web
RUN chown -R glider:glider /glider-dac-status/
USER glider
EXPOSE 5000
