#!/usr/bin/python3 -u

# http://www.fifi.org/doc/libapt-pkg-doc/method.html/index.html

import boto3
import sys
import logging
import os
from awscli.customizations.s3.utils import split_s3_bucket_key


MESSAGE_CODES = {
    100: 'Capabilities',
    101: 'General Logging',
    102: 'Status',
    200: 'URI Start',
    201: 'URI Done',
    400: 'URI Failure',
    401: 'General Failure',
    600: 'URI Acquire',
    601: 'Configuration',
}


DEBUG_LOG_PATH = '/home/ubuntu/s3-apt-log.txt'

def main():
    logging.basicConfig(level=logging.INFO, filename=DEBUG_LOG_PATH, filemode='w') # init logging
    output_to_apt(100, {'Version': '1.0', 'Single-Instance': 'true','Send-Config': 'true'}) # send capabilities
    secret_key, access_key = get_credentials() # get credentials from aws config
    valid_credentials = verify_credentials(secret_key, access_key) # verify user credentials valid
    if valid_credentials:
        client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        apt_message_loop(client)
    return 0


def output_to_apt(code, messages):
    output = '{0} {1}\n'.format(code, MESSAGE_CODES[code])
    for header in messages.keys():
        message = messages[header]
        output += '{0}: {1}\n'.format(header, message)
    sys.stdout.write(output + '\n')


def apt_message_loop(client):
    output = {}
    logging.info('in parse_aprt_output')
    while True:
        line = sys.stdin.readline()
        if not line:
            break
        if '600 URI Acquire' in line:
            uri = sys.stdin.readline()
            handle_uri_acquire(uri, client)
        logging.info(line)


def handle_uri_acquire(uri, client):
    logging.info('URI COOL {0}'.format(uri))
    


def get_credentials():
    username = os.environ['SUDO_USER']
    credentials_path = '/home/{0}/.aws/credentials'.format(username)
    credentials_file = open(credentials_path, mode = 'r')
    contents = credentials_file.readlines()
    secret_key = None
    access_key = None
    for line in contents:
        if 'aws_secret_access_key = ' in line:
            secret_key = line.split(' = ')[1]
        if 'aws_access_key_id = ' in line:
            access_key = line.split(' = ')[1]
    return secret_key, access_key


def verify_credentials(secret_key, access_key):
    valid = True
    if secret_key is None:
        output_to_apt(401, {'Message': 'Failed to find secret key'})
        valid = False
    if access_key is None:
        output_to_apt(401, {'Message': 'Failed to find access key'})
        valid = False

    logging.info('wow wee')

    return valid


if __name__ == '__main__':
    main()
