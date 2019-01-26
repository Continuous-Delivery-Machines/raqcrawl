"""Runs the Crawler with configuration given by the environment."""
import datetime
import ftplib
import inspect
import json
import os
import random
import shutil
import string
import sys
from subprocess import PIPE, run

import boto3
from botocore import exceptions

from github_session import GithubSession
from sqs_queue_capsuling import SqsMessageQueue


def debug(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    log(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, level=5)


def info(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    log(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, level=4)


def warn(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    log(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, level=2)


def error(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    log(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, level=1)


def conf_info(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
    log(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, level=1)


def log(*objects, sep=' ', end='\n', file=sys.stdout, flush=False, level=6):
    if level <= LOG_LEVEL:
        stuff = []
        timestamp = datetime.datetime.now().strftime('[%H:%M:%S]')
        caller = "[{}]".format(inspect.stack()[2].function)
        stuff.append(timestamp)
        stuff.append(caller)
        stuff.extend(objects)
        print(*stuff, sep=sep, end=end, flush=flush, file=sys.stderr)


def read_config_from_environment(stage: str = "DEV"):
    """Collects all environmental variables with a specific style and
    returns them as a dictionary."""
    base = "RAQ_CRAWLER_" + stage.upper() + "_"
    conf = dict()
    conf['STAGE'] = stage.lower()
    for key in (k for k in os.environ if k.startswith(base)):
        name = key[len(base):].lower()
        conf[name] = os.environ[key]
    return conf


def run_crawler_with_config(config, boto3_session):
    """Instantiates connections and instances, ties them together and runs the crawler."""
    global GLOBAL

    github_session = GithubSession()
    github_session.set_credentials(personal_access_token=config['github_token'])

    msg_queue = SqsMessageQueue(botosession=boto3_session,
                                wait_time=20,
                                queue_address=config['msg_queue_address'],
                                msg_visibility_timeout=30)

    my_prefix = 'raq_crawler_{}'.format(GLOBAL['RANDOM_ID'])

    working_path = '/tmp/{}'.format(my_prefix)
    results_path = working_path + '/results/'
    os.makedirs(working_path)
    os.makedirs(results_path)
    GLOBAL['ORIGIN_DIR'] = working_path
    while GLOBAL['SHOULD_RUN']:
        os.chdir(GLOBAL['ORIGIN_DIR'])
        message = msg_queue.pop_next_message()
        if github_session.rate is not None:
            info('Current rate left: {}'.format(github_session.rate))
            info('Resets at {}'.format(github_session.rate_reset_time.isoformat()))
        debug('Received Msg')
        debug(message.body_raw)

        if 'task_type' not in message.body_dict:
            warn("Received Message without task_type. '{}'\nIgnoring message and deleting it.".format(message.body_raw))
            message.delete()
        if message.body_dict['task_type'] == 'repo':
            handle_repo_task(github_session, message, working_path, results_path)
            message.delete()
        elif message.body_dict['task_type'] == 'refill':
            handle_refill_task(github_session, message, msg_queue)
            message.delete()
        elif message.body_dict['task_type'] == 'kill-15':
            error('Received kill-15 task.')
            GLOBAL['SHOULD_RUN'] = False
            msg_queue.write_message(message_dict={'task_type': 'kill-15'})


def upload_to_server(file_path):
    if not os.path.isfile(file_path):
        error("Source file {} does not exist")

    ip = CONFIG['ftp_address']
    uname = CONFIG['ftp_user']
    passw = CONFIG['ftp_password']
    ftp_conn = ftplib.FTP_TLS(ip)
    ftp_conn.login(user=uname, passwd=passw)
    ftp_conn.prot_p()

    file_name = file_path.split('/')[-1]

    target_path = "ftp/raq/results/{}".format(file_name)

    fh = open(file_path, 'rb')
    stor_cmd = 'STOR {}'.format(target_path)
    ftp_conn.storbinary(stor_cmd, fh)
    fh.close()


def handle_repo_task(github_session, message, working_path, results_path):
    delimiter = b'\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x7b'
    try:
        task = message.body_dict['repo_task']
        info('Received repo_task')
        debug(message.body_dict)
        debug(message.message_attributes)
    except FileExistsError as e:
        error(e)
        return 0x10

    warn('Working on repo with id {}'.format(task['id']))

    result_dict = {}

    repo_meta_dict, headers, resp_body = github_session.request_url(task['api_url'])

    result_dict['meta'] = repo_meta_dict

    languages_dict, languages_headers, languages_resp_body = github_session.request_url(repo_meta_dict['languages_url'])

    result_dict['languages'] = languages_dict

    try:
        repo_git_path = working_path + "/git_repo/"
        info("Cloning {} {}".format(repo_meta_dict['id'], repo_meta_dict['full_name']))
        clone_repository_into_directory(target_path=repo_git_path, clone_url=repo_meta_dict['clone_url'])
    except Exception as e:
        error('Aborting {}, {} because of error'.format(repo_meta_dict['id'], repo_meta_dict['full_name']))
        error(e)
        return

    os.chdir(repo_git_path)
    initial_sha = git_log_get_initial_sha()

    result_dict['commits'] = {}

    agenda = [initial_sha]
    done_shas = []
    for current_sha in agenda:
        debug('Working on sha {}'.format(current_sha))
        if current_sha in done_shas:
            continue
        if current_sha == '':
            continue

        result_dict['commits'][current_sha] = {}

        try:
            parents_exit_code, parents_out = git_parent_shas_space_separated(current_sha, delimiter)

            if parents_exit_code != 0:
                pass
            else:
                parent_shas = parents_out.split(" ")
                if len(parent_shas) == 1 and parent_shas[0] == '':
                    pass
                else:
                    agenda.extend(parent_shas)
                    result_dict['commits'][current_sha]['parents'] = parent_shas

            message_exit_code, message_out = git_show_commit_msg(current_sha, delimiter)

            if message_exit_code != 0:
                warn("Failed git_show_commit_msg with exit code {}\nRepo {}\nSHA {}\nDelimiter {}"
                     .format(message_exit_code, repo_meta_dict['id'], current_sha, delimiter))
                pass
            else:
                result_dict['commits'][current_sha]['message'] = message_out
                debug('Added {}'.format(message_out))

        except Exception as e:
            error("Exception occured")
            error(e)
        done_shas.append(current_sha)

    result_dict['CONFIG'] = CONFIG
    result_dict['GLOBAL'] = GLOBAL

    final_content = json.dumps(result_dict)
    result_json_f_path = results_path + '/{}.json'.format(result_dict['meta']['id'])
    result_json_f = open(result_json_f_path, 'w')
    result_json_f.write(final_content)
    result_json_f.flush()
    result_json_f.close()

    shutil.rmtree(repo_git_path)

    upload_to_server(result_json_f_path)

    info('Done with task for {}'.format(repo_meta_dict['id']))


def git_log_get_initial_sha():
    log_process = run(['git', '--no-pager', 'log', '--pretty=%H', '--max-count=1'],
                      stdout=PIPE, encoding='utf-8', universal_newlines=True)
    initial_sha = log_process.stdout
    if initial_sha[-1] == '\n':
        initial_sha = initial_sha[:-1]
    return initial_sha


def git_show_commit_msg(current_sha, delimiter):
    combi_format = '--pretty=%B{}'.format(delimiter.decode())
    show_commit_cmd = ['git', '--no-pager', 'show', '--shortstat', combi_format, current_sha]
    show_commit_proc = run(show_commit_cmd, stdout=PIPE, )
    show_commit_out_bytes = show_commit_proc.stdout
    show_commit_out_bytes_target = show_commit_out_bytes[:show_commit_out_bytes.find(delimiter)]
    show_commit_exit_code = show_commit_proc.returncode
    show_out = show_commit_out_bytes_target.decode('unicode-escape')
    return show_commit_exit_code, show_out


def git_parent_shas_space_separated(current_sha, delimiter):
    parents_format = '--pretty=format:%P{}'.format(delimiter.decode())
    parents_cmd = ['git', '--no-pager', 'show', '--shortstat', parents_format, current_sha]
    parents_proc = run(parents_cmd, stdout=PIPE, stderr=PIPE)
    parents_exit_code = parents_proc.returncode
    parents_out_bytes = parents_proc.stdout
    parents_out_bytes_target = parents_out_bytes[:parents_out_bytes.find(delimiter)]
    parents_out = parents_out_bytes_target.decode('unicode-escape')
    return parents_exit_code, parents_out


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

    info('Received refill_task')
    debug(message.body_dict)
    debug(message.message_attributes)
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
        debug('refill_task adding id {} for repo {}'.format(repo_dict['id'], repo_dict['full_name']))
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
    info('refill_task adding since id {} '.format(last_id))
    msg_queue.write_message(message_dict=task,
                            message_attributes_dict=task_attr)

    info('refill_task done')


def boto_session_and_sts_id(config):
    global GLOBAL
    ## Try boto3 without os variables, hoping for AWS instance
    try:
        botos = boto3.session.Session(region_name=config['region_name'])
        sts_identifier = botos.client('sts').get_caller_identity()
    except exceptions.NoCredentialsError as e:
        botos = boto3.session.Session(aws_access_key_id=config['aws_id'],
                                      aws_secret_access_key=config['aws_secret'],
                                      region_name=config['region_name'])
        sts_identifier = botos.client('sts').get_caller_identity()

    return botos, sts_identifier


if __name__ == '__main__':
    LOG_LEVEL = 2
    GLOBAL = {
        'START_TIMESTAMP': datetime.datetime.utcnow().isoformat(),
        'RANDOM_ID': ''.join(random.choices(string.ascii_letters + string.digits, k=32)),
        'SHOULD_RUN': True
    }

    conf_info("START_TIMESTAMP: {}".format(GLOBAL['START_TIMESTAMP']))
    conf_info("RANDOM_ID: {}".format(GLOBAL['RANDOM_ID']))

    if len(sys.argv) > 1:
        CONFIG = read_config_from_environment(sys.argv[1])
    else:
        CONFIG = read_config_from_environment()
    debug(CONFIG)

    boto3_session, sts_id = boto_session_and_sts_id(CONFIG)
    GLOBAL['STS_ARN'] = sts_id['Arn']

    run_crawler_with_config(CONFIG, boto3_session)
