#!/usr/bin/env python
# -*- coding: utf-8 -*-

import boto3
import json
import logging
import os
import time
from generate_profile_plot import generate_profile_plot

def main(SQS_URL):
    '''
    Main always running SQS queue processor
    '''
    sqs = boto3.client('sqs')
    while True:
        response = sqs.receive_message(
            QueueUrl = SQS_URL,
            MaxNumberOfMessages = 1,
        )
        if "Messages" not in response.keys():
            # if no messages, sleep for a few
            time.sleep(30)
            continue

        for msg in response["Messages"]: # not much need for 'for' but leave it in case we do up MaxNumberOfMessages
            try:
                receipt_handle = msg['ReceiptHandle']
                body           = msg['Body']
                try:
                    obj = json.loads(body)     # load as object
                    thredds_url = obj['thredds_url']
                    logging.info("Plotting from {}".format(thredds_url))
                    generate_profile_plot(thredds_url)
                except Exception:
                    logging.exception("processing error")

                finally: # always delete message
                    sqs.delete_message(QueueUrl=SQS_URL, ReceiptHandle=receipt_handle)

            except Exception: # per message exception
                logging.exception("message handling error")


if __name__ == "__main__":

    # setup logging
    dirname = os.path.dirname(os.path.realpath(__file__))
    logging_conf = os.path.join(dirname, 'logging.conf')
    if os.path.exists(logging_conf):
        import logging.config
        logging.config.fileConfig(logging_conf)
    else: # default logging
        logging.basicConfig(level=logging.INFO)

    try:
        SQS_URL = os.environ['SQS_URL']
        main(SQS_URL)
    except Exception as e: # this exception is if whole thing fails to run
        logging.exception("failed to start")
