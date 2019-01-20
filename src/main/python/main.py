"""Runs the Crawler with configuration given by the environment."""
import os
import sys

import boto3

from github_session import GithubSession
from sqs_queue_capsuling import SqsMessageQueue


def read_config_from_environment(stage: str = "DEV"):
    """Collects all environmental variables with a specific style and
    returns them as a dictionary."""
    base = "RAQ_CRAWLER_" + stage + "_"
    conf = dict()
    for key in (k for k in os.environ if k.startswith(base)):
        print(key)
        name = key[len(base):].lower()
        conf[name] = os.environ[key]
    return conf


def run_crawler_with_config(config):
    """Instantiates connections and instances, ties them together and runs the crawler."""
    github_session = GithubSession()
    github_session.set_credentials(personal_access_token=config['github_access_token'])

    boto3_session = boto3.session.Session(aws_access_key_id=config['aws_key'],
                                          aws_secret_access_key=config['aws_secret'],
                                          region_name=config['region_name'])

    msg_queue = SqsMessageQueue(botosession=boto3_session,
                                wait_time=20,
                                queue_address=config['msg_queue_address'],
                                msg_visibility_timeout=600)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        CONFIG = read_config_from_environment(sys.argv[1])
    else:
        CONFIG = read_config_from_environment()
        print(CONFIG)

    run_crawler_with_config(CONFIG)
