import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


CONFIG_TABLE_NAME = os.environ['CONFIG_TABLE_NAME']


def get_client(service):
    return boto3.client(service)


def get_resource(service):
    return boto3.resource(service)


def error_and_exit(event, error_msg='ERROR'):
    '''Throw error and exit'''

    logger.error(error_msg)


def lambda_handler(event, context):
    # print(event)
    print("Received input event: ", event)
    # repository_name = event['Input']['repositoryName']
    repository_name = event['repositoryName']
    print(repository_name)
    # reference_type = event['referenceType']
    reference_name = event['referenceName']
    # commit_id = event['commitId']

    ddb_resource = get_resource('dynamodb')
    table = ddb_resource.Table(CONFIG_TABLE_NAME)

    data = {}
    try:
        response = table.get_item(
            Key={
                'RepoName': repository_name,
                'RepoTag': reference_name
            }
        )
        if 'Item' in response:
            print("Item: ", response['Item'])

            output = {"StatusCode": "200",
                      # "reference_type": reference_type,
                      # "commit_id": commit_id,
                      "item": response['Item']}
            print("response: ", output)
            return output
            # return json.dumps(data)
        else:
            output = {"StatusCode": "500", "repository_name": repository_name,
                      # "reference_type": reference_type,
                      "reference_name": reference_name,
                      # "commit_id": commit_id,
                      "item": ""}
            return output
            # error_and_exit(event, 'No configuration found for reponame - repotag combination')
    except ClientError as e:
        error_and_exit(
            event, 'Error while getting information from configuration table')
