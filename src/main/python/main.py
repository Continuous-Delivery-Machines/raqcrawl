"""Runs the Crawler with configuration given by the environment."""
import datetime
import os
import random
import string
import subprocess
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

    my_prefix = 'raq_crawler_{}'.format(STATS['RANDOM_ID'])
    # working_temp_dir = tempfile.TemporaryDirectory()
    # working_path = working_temp_dir.name

    os.makedirs('/tmp/{}'.format(my_prefix))
    working_path = '/tmp/{}'.format(my_prefix)
    should_run = True
    STATS['ORIGIN_DIR'] = working_path
    while should_run:
        os.chdir(STATS['ORIGIN_DIR'])
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
            except FileExistsError as e:
                print(e)
            else:
                res_dict, headers, resp_body = github_session.request_url(task['api_url'])
                metaf_name = repo_path + "/meta.json"

                print('Metaf {}'.format(metaf_name))

                metaf = open(metaf_name, 'w')
                metaf.write(resp_body)
                metaf.flush()
                metaf.close()

                try:
                    repo_git_path = repo_path + "/git_repo/"
                    print("Cloning {}, {}".format(res_dict['id'], res_dict['full_name']))
                    pop = subprocess.run(['git', 'clone', res_dict['clone_url'], repo_git_path], universal_newlines=True)
                    pop.check_returncode()
                except Exception as e:
                    print('Aborting {}, {} because of error'.format(res_dict['id'], res_dict['full_name']))
                    print(e)
                else:
                    os.chdir(repo_git_path)
                    log_process = subprocess.run(['git', '--no-pager', 'log', '--pretty=%H', '--max-count=1'], stdout=subprocess.PIPE, encoding='utf-8', universal_newlines=True)
                    initial_sha = log_process.stdout
                    if initial_sha[-1] == '\n':
                        initial_sha = initial_sha[:-1]
                    agenda = [initial_sha]
                    done_shas = []
                    for current_sha in agenda:
                        if current_sha in done_shas:
                            continue
                        if current_sha == '':
                            continue
                        delimiter = '###wtf###'
                        parents_format = '--pretty=format:%P{}'.format(delimiter)
                        combi_format = '--pretty=%H %T %P %N{}'.format(delimiter)
                        show_commit_cmd = ['git', '--no-pager', 'show', '--shortstat', combi_format, current_sha]
                        parents_cmd = ['git', '--no-pager', 'show', '--shortstat', parents_format, current_sha]

                        try:
                            parents_proc = subprocess.run(parents_cmd, stdout=subprocess.PIPE, encoding='unicode-escape', universal_newlines=True, stderr=subprocess.PIPE)
                            parents_exit_code = parents_proc.returncode
                            parents_out = parents_proc.stdout

                            if parents_exit_code != 0:
                                pass
                            else:
                                if (delimiter + "\n") not in parents_out:
                                    pass
                                parent_shas = parents_out.split(delimiter)[0].split(" ")
                                if len(parent_shas) == 1 and parent_shas[0] == '':
                                    pass
                                agenda.extend(parent_shas)

                            show_commit_proc = subprocess.run(show_commit_cmd, stdout=subprocess.PIPE, encoding='unicode-escape')

                            show_commit_exit_code = show_commit_proc.returncode
                            show_out = show_commit_proc.stdout

                            if show_commit_exit_code != 0:
                                pass
                            else:
                                x = show_out.split(delimiter)
                                myout = x[0]
                                leftover = ''.join(x[1:])
                                shaf_name = repo_path + "/{}.json".format(current_sha)

                                print('shaf {}'.format(shaf_name))

                                shaf = open(shaf_name, 'w')
                                shaf.write(myout)
                                shaf.flush()
                                shaf.close()
                        except Exception as e:
                            print(e)
                            print(e)
                        done_shas.append(current_sha)
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
