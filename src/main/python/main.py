"""Runs the Crawler with configuration given by the environment."""
import datetime
import json
import os
import random
import string
import sys
from subprocess import PIPE, run

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
    global GLOBAL

    github_session = GithubSession()
    github_session.set_credentials(personal_access_token=config['github_token'])

    boto3_session = boto3.session.Session(aws_access_key_id=config['aws_id'],
                                          aws_secret_access_key=config['aws_secret'],
                                          region_name=config['region_name'])

    msg_queue = SqsMessageQueue(botosession=boto3_session,
                                wait_time=20,
                                queue_address=config['msg_queue_address'],
                                msg_visibility_timeout=30)

    my_prefix = 'raq_crawler_{}'.format(GLOBAL['RANDOM_ID'])
    # working_temp_dir = tempfile.TemporaryDirectory()
    # working_path = working_temp_dir.name

    os.makedirs('/tmp/{}'.format(my_prefix))
    working_path = '/tmp/{}'.format(my_prefix)
    GLOBAL['ORIGIN_DIR'] = working_path
    while GLOBAL['SHOULD_RUN']:
        os.chdir(GLOBAL['ORIGIN_DIR'])
        message = msg_queue.pop_next_message()
        if github_session.rate is not None:
            print('Current rate left: {}'.format(github_session.rate))
            print('Resets at {}'.format(github_session.rate_reset_time.isoformat()))
        print('Received Msg')
        print(message.body_raw)

        if 'task_type' not in message.body_dict:
            print(message.body_dict)
            print('bye bye')
            GLOBAL['SHOULD_RUN'] = False
        if message.body_dict['task_type'] == 'repo':
            handle_repo_task(github_session, message, working_path)
        elif message.body_dict['task_type'] == 'refill':
            handle_refill_task(github_session, message, msg_queue)
        elif message.body_dict['task_type'] == 'kill-15':
            GLOBAL['SHOULD_RUN'] = False
            msg_queue.write_message(message_dict={'task_type': 'stop'})
        message.delete()


def handle_repo_task(github_session, message, working_path):
    try:
        task = message.body_dict['repo_task']
        print('Received repo_task')
        print(message.body_dict)
        print(message.message_attributes)
        repo_task_path = working_path + "/{}".format(task['id'])
        os.makedirs(repo_task_path)
    except FileExistsError as e:
        print(e)
        return 0x10

    result_dict = {}

    repo_meta_dict, headers, resp_body = github_session.request_url(task['api_url'])
    meta_json_full_file_name = repo_task_path + "/meta.json"
    #print('Meta.json {}'.format(meta_json_full_file_name))
    #write_meta_json(meta_json_full_file_name, resp_body)

    result_dict['meta'] = repo_meta_dict

    try:
        repo_git_path = repo_task_path + "/git_repo/"
        print("Cloning {} {}".format(repo_meta_dict['id'], repo_meta_dict['full_name']))
        clone_repository_into_directory(target_path=repo_git_path, clone_url=repo_meta_dict['clone_url'])
    except Exception as e:
        print('Aborting {}, {} because of error'.format(repo_meta_dict['id'], repo_meta_dict['full_name']))
        print(e)
        return

    os.chdir(repo_git_path)
    log_process = run(['git', '--no-pager', 'log', '--pretty=%H', '--max-count=1'],
                      stdout=PIPE, encoding='utf-8', universal_newlines=True)
    initial_sha = log_process.stdout

    if initial_sha[-1] == '\n':
        initial_sha = initial_sha[:-1]

    result_dict['commits'] = []

    agenda = [initial_sha]
    done_shas = []
    for current_sha in agenda:
        print('Working on sha {}'.format(current_sha))
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
            parents_proc = run(parents_cmd, stdout=PIPE, encoding='unicode-escape',
                               universal_newlines=True, stderr=PIPE)
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

            show_commit_proc = run(show_commit_cmd, stdout=PIPE,
                                   encoding='unicode-escape')

            show_commit_exit_code = show_commit_proc.returncode
            show_out = show_commit_proc.stdout

            if show_commit_exit_code != 0:
                pass
            else:
                x = show_out.split(delimiter)
                myout = x[0]
                leftover = ''.join(x[1:])
                shaf_name = repo_task_path + "/{}.json".format(current_sha)

                result_dict['commits'].append({'content': myout})

                print('Added {}'.format(myout))
                # print('shaf {}'.format(shaf_name))
                #
                # shaf = open(shaf_name, 'w')
                # shaf.write(myout)
                # shaf.flush()
                # shaf.close()
        except Exception as e:
            print(e)
        done_shas.append(current_sha)

    final_content = json.dumps(result_dict)
    repo_f = open(repo_task_path + '/result.json', 'w')
    repo_f.write(final_content)
    repo_f.flush()
    repo_f.close()
    print('Done')


def clone_repository_into_directory(target_path: str, clone_url: str):
    pop = run(['git', 'clone', clone_url, target_path], universal_newlines=True)
    pop.check_returncode()


def write_meta_json(metaf_name, resp_body):
    metaf = open(metaf_name, 'w')
    metaf.write(resp_body)
    metaf.flush()
    metaf.close()


def handle_refill_task(github_session, message, msg_queue):
    global GLOBAL

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
                'StringValue': GLOBAL['RANDOM_ID']
            },
            'creator_started_timestamp': {
                'DataType': "String",
                'StringValue': GLOBAL['START_TIMESTAMP']
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
            'StringValue': GLOBAL['RANDOM_ID']
        },
        'creator_started_timestamp': {
            'DataType': "String",
            'StringValue': GLOBAL['START_TIMESTAMP']
        },
    }
    print('refill_task adding since id {} '.format(last_id))
    msg_queue.write_message(message_dict=task,
                            message_attributes_dict=task_attr)

    print('refill_task done')


if __name__ == '__main__':
    GLOBAL = {
        'START_TIMESTAMP': datetime.datetime.utcnow().isoformat(),
        'RANDOM_ID': ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
        'SHOULD_RUN': True
    }
    print("START_TIMESTAMP: {}".format(GLOBAL['START_TIMESTAMP']))
    print("RANDOM_ID: {}".format(GLOBAL['RANDOM_ID']))
    if len(sys.argv) > 1:
        CONFIG = read_config_from_environment(sys.argv[1])
    else:
        CONFIG = read_config_from_environment()
        print(CONFIG)

    run_crawler_with_config(CONFIG)
