from __future__ import annotations
from __future__ import print_function

import os

from botocore.exceptions import ClientError
import logging
import boto3
import json

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_client(service):
    return boto3.client(service)


def error_and_exit(event, error_msg='ERROR'):
    '''Throw error and exit'''

    logger.error(error_msg)


def lambda_handler(event, context):
    print(event)
    alpha_aws_account_id = ''
    beta_aws_account_id = ''
    gamma_aws_account_id = ''
    prod_aws_account_id = ''
    alpha_aws_account_id = ''
    beta_aws_account_id = ''
    gamma_aws_account_id = ''
    prod_aws_account_id = ''
    # s3_bucket_name = event['Item']['S3BucketName']
    # s3_bucket_prefix = event['Item']['S3BucketPrefix']
    s3_bucket_name = os.environ['CFN_TEMPLATE_BUCKET_NAME']
    s3_bucket_prefix = os.environ['CFN_TEMPLATE_BUCKET_PREFIX']
    pipeline_name = event['Item']['RepoName'] + event['Item']['RepoTag']
    repository_name = event['Item']['RepoName']
    repository_tag = event['Item']['RepoTag']
    build_spec_file = event['Item']['BuildSpecFile']
    build_image_name = event['Item']['BuildImage']

    la_create_stack_parameters = []
    for keys in event['Item']['DeploymentConfigurations']:
        dict_value = event['Item']['DeploymentConfigurations']
        if type(dict_value[keys]) is dict:
            for item in dict_value[keys]:
                item_value = dict_value[keys][item]
                if type(dict_value[keys][item]) is dict:
                    for key in dict_value[keys][item]:
                        if type(dict_value[keys][item]) is dict:
                            for keyi in dict_value[keys][item]:
                                if type(dict_value[keys][item][keyi]) is dict:
                                    for k in dict_value[keys][item][keyi]:
                                        d = {"ParameterKey": k, "ParameterValue": dict_value[keys][item][keyi][k]}
                                        if d not in la_create_stack_parameters:
                                            la_create_stack_parameters.append(
                                                {"ParameterKey": k, "ParameterValue": dict_value[keys][item][keyi][k]})
                                else:
                                    la_create_stack_parameters.append(
                                        {"ParameterKey": keyi, "ParameterValue": dict_value[keys][item][keyi]})
                        else:
                            print('key is ', key + " with value ", dict_value[keys][item][key])
                            la_create_stack_parameters.append(
                                {"ParameterKey": item, "ParameterValue": dict_value[keys][item]})
                else:
                    la_create_stack_parameters.append({"ParameterKey": item, "ParameterValue": dict_value[keys][item]})
        elif type(dict_value[keys]) is str:
            la_create_stack_parameters.append({"ParameterKey": keys, "ParameterValue": dict_value[keys]})
    la_create_stack_parameters.append({"ParameterKey": "RepoName", "ParameterValue": repository_name})
    la_create_stack_parameters.append({"ParameterKey": "RepoTag", "ParameterValue": repository_tag})
    la_create_stack_parameters.append({"ParameterKey": "BuildSpecFile", "ParameterValue": build_spec_file})
    la_create_stack_parameters.append({"ParameterKey": "BuildImage", "ParameterValue": build_image_name})
    
    print(la_create_stack_parameters)

    for dic in la_create_stack_parameters:
        for key in dic:
            if dic[key] == 'AlphaAwsAccountId':
                alpha_aws_account_id = dic['ParameterValue']
            if dic[key] == 'BetaAwsAccountId':
                beta_aws_account_id = dic['ParameterValue']
            if dic[key] == 'GammaAwsAccountId':
                gamma_aws_account_id = dic['ParameterValue']
            if dic[key] == 'ProdAwsAccountId':
                prod_aws_account_id = dic['ParameterValue']

    alpha_child_account_deployer_role_arn = 'arn:aws:iam::' + alpha_aws_account_id + ':role/ChildAccountDeployerRole'
    beta_child_account_deployer_role_arn = 'arn:aws:iam::' + beta_aws_account_id + ':role/ChildAccountDeployerRole'
    gamma_child_account_deployer_role_arn = 'arn:aws:iam::' + gamma_aws_account_id + ':role/ChildAccountDeployerRole'
    prod_child_account_deployer_role_arn = 'arn:aws:iam::' + prod_aws_account_id + ':role/ChildAccountDeployerRole'
    alpha_child_account_formation_role_arn = 'arn:aws:iam::' + alpha_aws_account_id + ':role/ChildAccountFormationRole'
    beta_child_account_formation_role_arn = 'arn:aws:iam::' + beta_aws_account_id + ':role/ChildAccountFormationRole'
    gamma_child_account_formation_role_arn = 'arn:aws:iam::' + gamma_aws_account_id + ':role/ChildAccountFormationRole'
    prod_child_account_formation_role_arn = 'arn:aws:iam::' + prod_aws_account_id + ':role/ChildAccountFormationRole' 

    la_create_stack_parameters.append({"ParameterKey": 'AlphaChildAccountDeployerRoleArn', "ParameterValue": alpha_child_account_deployer_role_arn})
    la_create_stack_parameters.append({"ParameterKey": 'BetaChildAccountDeployerRoleArn', "ParameterValue": beta_child_account_deployer_role_arn})
    la_create_stack_parameters.append({"ParameterKey": 'GammaChildAccountDeployerRoleArn', "ParameterValue": gamma_child_account_deployer_role_arn})
    la_create_stack_parameters.append({"ParameterKey": 'ProdChildAccountDeployerRoleArn', "ParameterValue": prod_child_account_deployer_role_arn})
    la_create_stack_parameters.append({"ParameterKey": 'AlphaChildAccountFormationRoleArn', "ParameterValue": alpha_child_account_formation_role_arn})
    la_create_stack_parameters.append({"ParameterKey": 'BetaChildAccountFormationRoleArn', "ParameterValue": beta_child_account_formation_role_arn})
    la_create_stack_parameters.append({"ParameterKey": 'GammaChildAccountFormationRoleArn', "ParameterValue": gamma_child_account_formation_role_arn})
    la_create_stack_parameters.append({"ParameterKey": 'ProdChildAccountFormationRoleArn', "ParameterValue": prod_child_account_formation_role_arn})
    la_create_stack_parameters.append({"ParameterKey": 'PipelineName', "ParameterValue": pipeline_name})

    stack_name = pipeline_name + "-stack"
    stack_not_exist = "Stack with id " + stack_name + " does not exist"

    client = get_client('cloudformation')

    try: 
        describe_stack_response = client.describe_stacks(
            StackName=stack_name
        )
        print(describe_stack_response["Stacks"][0]["StackStatus"])
        stack_status = describe_stack_response["Stacks"][0]["StackStatus"]
        if stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']:
            update_stack_response = client.update_stack(
                StackName=stack_name,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                TemplateURL='https://' + s3_bucket_name + '.s3.amazonaws.com' + '/' + s3_bucket_prefix + '/codepipeline.yaml',
                Parameters=la_create_stack_parameters
            )
            print('Updating Stack with stack Id', update_stack_response)
        elif stack_status in ['DELETE_FAILED']:
            print('Stack in delete failed state')
    except ClientError as e:
            print(e.response['Error'])
            if e.response['Error']['Message'] == 'No updates are to be performed.':
                print('No updates are to be performed')
            elif e.response['Error']['Message'] == stack_not_exist:
                create_stack_response = client.create_stack(
                StackName=stack_name,
                Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
                OnFailure='DELETE',
                TemplateURL='https://' + s3_bucket_name + '.s3.amazonaws.com' + '/' + s3_bucket_prefix + '/codepipeline.yaml',
                Parameters=la_create_stack_parameters
                )
                print('Creating '+stack_name)
            else:
                print('Please fix the exception to continue')