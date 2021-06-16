#!/usr/bin/env python3

# http://www.fifi.org/doc/libapt-pkg-doc/method.html/index.html

import boto3
import sys

MESSAGE_CODES = {
    100: 'Capabilities',
    102: 'Status',
    200: 'URI Start',
    201: 'URI Done',
    400: 'URI Failure',
    401: 'General Failure',
    600: 'URI Acquire',
    601: 'Configuration',
}


def main():
    verify_credentials()
    return 0


def output_to_apt(code, messages):
    output = '{0} {1}\n'.format(code, MESSAGE_CODES[code])
    for header in messages.keys():
        message = messages[header]
        output += '{0}: {1}\n'.format(header, message)
    sys.stdout.write(output)


def verify_credentials():
    client = boto3.client('sts')
    try:
        client.get_caller_identity()
    except:
        output_to_apt(401, {'Message': 'Failed to authenticate, verify your credentials.'})
    

if __name__ == '__main__':
    main()
