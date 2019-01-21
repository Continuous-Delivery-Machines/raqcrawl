"""Runs the Crawler with configuration given by the environment."""
import datetime
import os
import random
import string
import sys
import tempfile

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
    global STATS

    github_session = GithubSession()
    github_session.set_credentials(personal_access_token=config['github_token'])

    boto3_session = boto3.session.Session(aws_access_key_id=config['aws_id'],
                                          aws_secret_access_key=config['aws_secret'],
                                          region_name=config['region_name'])

    msg_queue = SqsMessageQueue(botosession=boto3_session,
                                wait_time=20,
                                queue_address=config['msg_queue_address'],
                                msg_visibility_timeout=30)

    working_temp_dir = tempfile.TemporaryDirectory(prefix='raq_crawler_{}'.format(STATS['RANDOM_ID']))
    working_path = working_temp_dir.name

    should_run = True

    while should_run:
        message = msg_queue.pop_next_message()
        if github_session.rate is not None:
            print('Current rate left: {}'.format(github_session.rate))
            print('Resets at {}'.format(github_session.rate_reset_time.isoformat()))
        print('Received Msg')
        print(message.body_raw)

        if 'task_type' not in message.body_dict:
            print(message.body_dict)
            print('bye bye')
            should_run = False
        if message.body_dict['task_type'] == 'repo':
            try:
                print('Received repo_task')
                print(message.body_dict)
                print(message.message_attributes)

                task = message.body_dict['repo_task']

                repo_path = working_path + "/{}".format(task['id'])
                os.makedirs(repo_path)

                res_dict, headers, resp_body = github_session.request_url(task['api_url'])
                metaf_name = repo_path + "/meta.json"

                print('Metaf {}'.format(metaf_name))

                metaf = open(metaf_name, 'w')
                metaf.write(resp_body)
                metaf.flush()
                metaf.close()
            except FileExistsError as e:
                print(e)
            print('Done')
        elif message.body_dict['task_type'] == 'refill':
            handle_refill_task(github_session, message, msg_queue)
        elif message.body_dict['task_type'] == 'kill-15':
            should_run = False
            msg_queue.write_message(message_dict={'task_type': 'stop'})
        message.delete()


def handle_refill_task(github_session, message, msg_queue):
    global STATS

    print('Received refill_task')
    print(message.body_dict)
    print(message.message_attributes)
    url = "https://api.github.com/repositories?since={}".format(message.body_dict['refill_task']['since_id'])
    res_dict, headers, resp_body = github_session.request_url(url)
    last_id = 0
    for repo_dict in res_dict:
        task = {
            'task_type': 'repo',
            'repo_task': {
                'id': repo_dict['id'],
                'full_name': repo_dict['full_name'],
                'api_url': "https://api.github.com/repos/{}".format(repo_dict['full_name'])
            }
        }
        task_attr = {
            'creator_id': {
                'DataType': "String",
                'StringValue': STATS['RANDOM_ID']
            },
            'creator_started_timestamp': {
                'DataType': "String",
                'StringValue': STATS['START_TIMESTAMP']
            },
        }
        last_id = int(repo_dict['id'])
        print('refill_task adding id {} for repo {}'.format(repo_dict['id'], repo_dict['full_name']))
        msg_queue.write_message(message_dict=task,
                                message_attributes_dict=task_attr)
    task = {
        'task_type': 'refill',
        'refill_task': {
            'since_id': last_id,
        }
    }
    task_attr = {
        'creator_id': {
            'DataType': "String",
            'StringValue': STATS['RANDOM_ID']
        },
        'creator_started_timestamp': {
            'DataType': "String",
            'StringValue': STATS['START_TIMESTAMP']
        },
    }
    print('refill_task adding since id {} '.format(last_id))
    msg_queue.write_message(message_dict=task,
                            message_attributes_dict=task_attr)

    print('refill_task done')


if __name__ == '__main__':
    STATS = {
        'START_TIMESTAMP': datetime.datetime.utcnow().isoformat(),
        'RANDOM_ID': ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    }
    print("START_TIMESTAMP: {}".format(STATS['START_TIMESTAMP']))
    print("RANDOM_ID: {}".format(STATS['RANDOM_ID']))
    if len(sys.argv) > 1:
        CONFIG = read_config_from_environment(sys.argv[1])
    else:
        CONFIG = read_config_from_environment()
        print(CONFIG)

    run_crawler_with_config(CONFIG)
