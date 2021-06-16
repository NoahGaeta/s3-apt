#!/usr/bin/env python3

import boto3

def main():
    client = boto3.client('s3')

    print(client)

    return 0


if __name__ == '__main__':
    main()
