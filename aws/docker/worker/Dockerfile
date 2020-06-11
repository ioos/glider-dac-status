FROM python:3.6
LABEL maintainer "RPS <devops@rpsgroup.com>"

ARG glider_gid_uid=1000

COPY . /glider-dac
WORKDIR glider-dac

RUN apt-get update && \
    apt-get install -y python3-netcdf4 && \
    pip install --no-cache cython && \
    pip install --no-cache -r requirements.txt && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -g $glider_gid_uid glider && \
    useradd -u $glider_gid_uid -g $glider_gid_uid glider

RUN chown -R glider:glider /glider-dac
USER glider

CMD ["python3", "queue_processor.py"]