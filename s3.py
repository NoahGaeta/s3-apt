#!/usr/bin/python3 -u

# http://www.fifi.org/doc/libapt-pkg-doc/method.html/index.html

import boto3
import sys
import logging
import os
import hashlib
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
    logging.info('creds\nSECRET: {0}\nACCESS_KEY: {1}\n'.format(secret_key, access_key))
    if valid_credentials:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        client = session.resource('s3', region_name='us-east-2')
        uri, filename = apt_message_loop()
        handle_uri_acquire(uri, filename, client)
    return 0


def output_to_apt(code, messages):
    output = '{0} {1}\n'.format(code, MESSAGE_CODES[code])
    for header in messages.keys():
        message = messages[header]
        output += '{0}: {1}\n'.format(header, message)
    logging.info('\nOUTPUT\n' + output + '\n')
    sys.stdout.write(output + '\n')


def apt_message_loop():
    output = {}
    logging.info('in parse_aprt_output')
    uri = None
    filename = None
    while True:
        line = sys.stdin.readline()
        logging.info('STDIN: {0}'.format(line))
        if '600 URI Acquire' in line:
            uri = sys.stdin.readline().rstrip().replace('URI: ', '')
            filename = sys.stdin.readline().rstrip().replace('Filename: ', '')
            break
    return uri, filename


def split_s3_path(s3_path):
    path_parts = s3_path.replace('s3://','').split('/')
    bucket = path_parts.pop(0)
    key = '/'.join(path_parts)
    return bucket.rstrip(), key.rstrip()


def handle_uri_acquire(uri, filename, client):
    logging.info('URI COOL {0}'.format(uri))
    bucket, key = split_s3_path(uri)
    s3_object = client.Bucket(bucket).Object(key)
    logging.info('BUCKET {0} KEY {1}'.format(bucket, key))
    try:
        response = s3_object.get()
        output_to_apt(200, {'URI': uri, 'Last-Modified': response['LastModified'].isoformat(), 'Size': response['ContentLength']})
        body_bytes = response['Body'].read()
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        sha256 = hashlib.sha256()
        sha512 = hashlib.sha512()
        output_file = open(filename, 'wb')
        output_file.write(body_bytes)
        md5.update(body_bytes)
        sha1.update(body_bytes)
        sha256.update(body_bytes)
        sha512.update(body_bytes)
        output_to_apt(201, 
                {'URI': uri, 
                'Last-Modified': response['LastModified'].isoformat(), 
                'Size': response['ContentLength'], 
                'MD5-Hash': md5.hexdigest(), 
                'MD5Sum-Hash': md5.hexdigest(), 
                'SHA1-Hash': sha1.hexdigest(), 
                'SHA256-Hash': sha256.hexdigest(),
                'SHA512-Hash': sha512.hexdigest()}
        )
    except Exception as e:
        logging.info(e)
        output_to_apt(400, {'Message': 'Failed during acquire', 'URI': uri})


def get_credentials():
    username = os.environ['SUDO_USER']
    credentials_path = '/home/{0}/.aws/credentials'.format(username)
    credentials_file = open(credentials_path, mode = 'r')
    contents = credentials_file.readlines()
    secret_key = None
    access_key = None
    for line in contents:
        if 'aws_secret_access_key = ' in line:
            secret_key = line.split(' = ')[1].rstrip()
        if 'aws_access_key_id = ' in line:
            access_key = line.split(' = ')[1].rstrip()
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
    sys.exit(main())
