from __future__ import annotations
from __future__ import print_function
from botocore.exceptions import ClientError
import logging
import boto3
import json
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_client(service):
    return boto3.client(service)


def error_and_exit(event, error_msg='ERROR'):
    '''Throw error and exit'''

    logger.error(error_msg)


def lambda_handler(event, context):
    print('Event Received', event)
    stream_records = event['Records']
    for record in stream_records:
        repo_name = record['dynamodb']['Keys']['RepoName']['S']
        repo_tag = record['dynamodb']['Keys']['RepoTag']['S']
        if record['eventName'] in ['MODIFY', 'INSERT']:
            print('Stream for RepoName {} and RepoTag {} '.format(repo_name, repo_tag))
            payload = {
                "repositoryName": repo_name,
                "referenceName": repo_tag
            }

            sfn_client = get_client('stepfunctions')
            try:
                sfn_client.start_execution(
                    stateMachineArn=os.environ['SFN_ARN'],
                    input=json.dumps(payload)
                )
            except sfn_client.exceptions.InvalidArn:
                print('Invalid ARN of the state machine')
            except sfn_client.exceptions.InvalidExecutionInput:
                print('Invalid input passed to the state machine')
            except sfn_client.exceptions.StateMachineDoesNotExist:
                print('State Machine does not exist')
            except ClientError as exception:
                print('Exception occurred ', exception)
        elif record['eventName'] in ['REMOVE']:
            cfn_client = get_client('cloudformation')
            stack_name = repo_name+repo_tag+"-stack"
            try:
                cfn_client.delete_stack(
                    StackName=stack_name
                )
            except ClientError as exception:
                print('Exception occurred ', exception)

