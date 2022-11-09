# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import (
    Duration,
    Stack,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_dynamodb as dynamodb,
    aws_stepfunctions as stepfunctions,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_iam as iam,
    aws_lambda_event_sources as lambda_event_sources,
    aws_s3_deployment as s3_deployment,

)
from constructs import Construct
import boto3


class DynamicPipelineStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        s3artifact_bucket = s3.Bucket(self, "PipelineArtifactBucket")

        sts_client = boto3.client('sts')
        account_id = sts_client.get_caller_identity().get('Account')
        template_bucket_name = "cloudformation-template-bucket-" + account_id

        cfn_template_bucket = s3.Bucket(self, "CfnTemplateBucket", bucket_name=template_bucket_name)

        s3_deployment.BucketDeployment(self, "CfnDeployment",
                                       sources=[s3_deployment.Source.asset("./cloudformations")],
                                       destination_bucket=cfn_template_bucket, destination_key_prefix="template",
                                       )
        # DynamoDB configuration table
        config_table = dynamodb.Table(self, "ConfigurationTable",
                                      partition_key=dynamodb.Attribute(name="RepoName",
                                                                       type=dynamodb.AttributeType.STRING),
                                      sort_key=dynamodb.Attribute(
                                          name="RepoTag", type=dynamodb.AttributeType.STRING),
                                      billing_mode=dynamodb.BillingMode.PROVISIONED,
                                      table_name="devops-pipeline-table-info",
                                      stream=dynamodb.StreamViewType.NEW_IMAGE
                                      )
        # role for cfnstack lambda
        cfnstack_lambda_role = iam.Role(self, "CfnRole",
                                        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                        description="Role for cloudformation create lambda")

        cfnstack_lambda_role.attach_inline_policy(iam.Policy(self, "CfnRolePolicy",
                                                             statements=[iam.PolicyStatement(
                                                                 actions=[
                                                                     "cloudformation:CreateChangeSet",
                                                                     "cloudformation:UpdateStack",
                                                                     "cloudformation:DescribeChangeSet",
                                                                     "cloudformation:ExecuteChangeSet",
                                                                     "cloudformation:DescribeStackResources",
                                                                     "cloudformation:DescribeStacks",
                                                                     "cloudformation:RollbackStack",
                                                                     "cloudformation:GetTemplate",
                                                                     "cloudformation:DeleteStack",
                                                                     "cloudformation:ValidateTemplate",
                                                                     "cloudformation:ListStacks",
                                                                     "cloudformation:DescribeStackSet",
                                                                     "cloudformation:CreateStack",
                                                                     "cloudformation:GetTemplateSummary",
                                                                     "cloudformation:ListChangeSets",
                                                                     "s3:CreateBucket",
                                                                     "s3:PutBucketAcl",
                                                                     "s3:Describe*",
                                                                     "s3:DeleteBucketPolicy",
                                                                     "s3:GetObject",
                                                                     "s3:ListBucket",
                                                                     "s3:GetBucketPolicy",
                                                                     "s3:PutEncryptionConfiguration",
                                                                     "s3:GetEncryptionConfiguration",
                                                                     "s3:PutBucketPublicAccessBlock",
                                                                     "s3:PutBucketPolicy",
                                                                     "kms:Get*",
                                                                     "kms:Put*",
                                                                     "kms:ScheduleKeyDeletion",
                                                                     "kms:Enable*",
                                                                     "kms:DescribeKey",
                                                                     "kms:CreateKey",
                                                                     "kms:Update*",
                                                                     "kms:Disable*",
                                                                     "iam:CreateRole",
                                                                     "iam:PutRolePolicy",
                                                                     "iam:ListPolicies",
                                                                     "iam:GetRole",
                                                                     "iam:DeleteRole",
                                                                     "iam:GetRolePolicy",
                                                                     "iam:TagRole",
                                                                     "iam:PassRole",
                                                                     "iam:DeleteRolePolicy",
                                                                     "iam:ListRoles",
                                                                     "iam:UpdateRole",
                                                                     "codebuild:UpdateProject",
                                                                     "codepipeline:GetPipeline",
                                                                     "sns:Subscribe",
                                                                     "sns:CreateTopic",
                                                                     "sns:DeleteTopic",
                                                                     "sns:GetTopicAttributes",
                                                                     "codepipeline:StartPipelineExecution",
                                                                     "codepipeline:UpdatePipeline",
                                                                     "codepipeline:CreatePipeline",
                                                                     "codepipeline:DeletePipeline",
                                                                     "codepipeline:GetPipelineState",
                                                                     "codebuild:CreateProject",
                                                                     "codebuild:StopBuild",
                                                                     "codebuild:CreateReport",
                                                                     "codebuild:DeleteProject"
                                                                 ],
                                                                 resources=["*"]
                                                             )]
                                                             ))

        # step function trigger lambda role
        step_function_trigger_lambda_role = iam.Role(self, "TriggerLambdaRole",
                                                     assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                     description="Role for trigger lambda")

        # Event Filter Lambda
        codecommit_event_filter = _lambda.Function(self, "EventFilterLambda", runtime=_lambda.Runtime.PYTHON_3_9,
                                                   handler="codecommit_event_filter.lambda_handler",
                                                   timeout=Duration.minutes(2),
                                                   environment={
                                                       "CONFIG_TABLE_NAME": config_table.table_name},
                                                   code=_lambda.Code.from_asset("lambda/eventfilter"))

        # CloudFormation initiation stack
        cfn_initiator_lambda = _lambda.Function(self, "CfnStack", runtime=_lambda.Runtime.PYTHON_3_9,
                                                handler="cfn_stack_create.lambda_handler", role=cfnstack_lambda_role,
                                                timeout=Duration.minutes(2),
                                                environment={
                                                    "CFN_TEMPLATE_BUCKET_NAME": template_bucket_name,
                                                    "CFN_TEMPLATE_BUCKET_PREFIX": "template"
                                                },
                                                code=_lambda.Code.from_asset("lambda/cfnstack"))

        # grant lambda access to dynamodb
        config_table.grant_read_write_data(codecommit_event_filter)

        # step function creation

        pass_state = stepfunctions.Pass(self, 'Collect Information',
                                        parameters=({
                                            "repositoryName": stepfunctions.JsonPath.string_at(
                                                "$.repositoryName"),
                                            "referenceName": stepfunctions.JsonPath.string_at("$.referenceName")
                                        })
                                        )

        pull_information_from_ddb = sfn_tasks.LambdaInvoke(
            self, "Get Mapping Information", lambda_function=codecommit_event_filter,
            payload=stepfunctions.TaskInput.from_object({
                "repositoryName": stepfunctions.JsonPath.string_at(
                    "$.repositoryName"),
                "referenceName": stepfunctions.JsonPath.string_at("$.referenceName")
            }),
            output_path="$",
            result_selector={
                "StatusCode": stepfunctions.JsonPath.string_at("$.Payload.StatusCode"),
                "Item": stepfunctions.JsonPath.string_at("$.Payload.item")
            }
        )

        kickoff_cloudformation_stack = sfn_tasks.LambdaInvoke(
            self, 'Initiate CloudFormation Stack', lambda_function=cfn_initiator_lambda,

        )

        is_successful = stepfunctions.Succeed(
            self, 'Successful', comment='Successful Execution')

        step_definition = pass_state.next(pull_information_from_ddb).next(
            stepfunctions.Choice(self, 'Deployment Configurations Exist?')
            .when(stepfunctions.Condition.string_equals("$.StatusCode", "200"), kickoff_cloudformation_stack)
            .when(stepfunctions.Condition.string_equals("$.StatusCode", "500"), is_successful)
            .otherwise(is_successful))

        state_machine = stepfunctions.StateMachine(self, 'StateMachine', definition=step_definition,
                                                   state_machine_name='pipeline-orchestrator')

        step_function_trigger_lambda_role.attach_inline_policy(
            iam.Policy(self, "StateMachinePolicy",
                       statements=[
                           iam.PolicyStatement(
                               actions=[
                                   "states:SendTaskSuccess",
                                   "states:ListStateMachines",
                                   "states:ListActivities"
                               ],
                               resources=["*"]
                           ),
                           iam.PolicyStatement(
                               actions=[
                                   "states:StartExecution"
                               ],
                               resources=[state_machine.state_machine_arn]
                           )
                       ]

                       )
        )

        step_function_trigger_lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'))

        step_function_trigger_lambda_role.attach_inline_policy(iam.Policy(self, "TriggerLambdaCfnRolePolicy",
                                                                          statements=[iam.PolicyStatement(
                                                                              actions=[
                                                                                  "cloudformation:ListStacks",
                                                                                  "cloudformation:DescribeStackResources",
                                                                                  "cloudformation:CreateChangeSet",
                                                                                  "cloudformation:GetTemplateSummary",
                                                                                  "cloudformation:DescribeStacks",
                                                                                  "cloudformation:RollbackStack",
                                                                                  "cloudformation:DescribeStackSet",
                                                                                  "cloudformation:CreateStack",
                                                                                  "cloudformation:GetTemplate",
                                                                                  "cloudformation:DeleteStack",
                                                                                  "cloudformation:UpdateStack",
                                                                                  "cloudformation:DescribeChangeSet",
                                                                                  "cloudformation:ExecuteChangeSet",
                                                                                  "cloudformation:ValidateTemplate",
                                                                                  "cloudformation:ListChangeSets",
                                                                                  "s3:ListBucket",
                                                                                  "s3:GetObject",
                                                                                  "s3:DeleteBucket",
                                                                                  "codepipeline:DeletePipeline",
                                                                                  "s3:DeleteBucketPolicy",
                                                                                  "SNS:DeleteTopic",
                                                                                  "iam:DeleteRolePolicy",
                                                                                  "codebuild:DeleteProject",
                                                                                  "kms:ScheduleKeyDeletion",
                                                                                  "kms:DescribeKey",
                                                                                  "iam:DeleteRole",
                                                                                  "SNS:GetTopicAttributes",
                                                                                  "codepipeline:GetPipeline"

                                                                              ],
                                                                              resources=["*"]
                                                                          )]
                                                                          ))
        print('State Machin Arn ', state_machine.state_machine_arn)
        # streamer lambda
        step_function_trigger_lambda = _lambda.Function(self, "StepFunctionTrigger", runtime=_lambda.Runtime.PYTHON_3_9,
                                                        handler="step_fn_starter.lambda_handler",
                                                        timeout=Duration.minutes(2),
                                                        environment={
                                                            "SFN_ARN": state_machine.state_machine_arn},
                                                        role=step_function_trigger_lambda_role,
                                                        code=_lambda.Code.from_asset("lambda/streamer"))

        step_function_trigger_lambda.add_event_source(lambda_event_sources.DynamoEventSource(
            config_table, starting_position=_lambda.StartingPosition.TRIM_HORIZON,
            batch_size=1
        ))
        # grant lambda access to dynamodb
        config_table.grant_read_write_data(step_function_trigger_lambda)
