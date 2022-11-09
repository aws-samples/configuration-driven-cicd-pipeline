# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import aws_cdk.pipelines
from aws_cdk import Stack
from constructs import Construct
from aws_cdk import aws_codecommit

from dynamic_pipeline.cdk_pipeline_stage import CdkPipelineStage


class CdkPipelineStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # # creates a code commit repo

        
        repo = aws_codecommit.Repository.from_repository_name(self, "BlogInfrastructure", "BlogInfrastructure")
        

        pipeline = aws_cdk.pipelines.CodePipeline(
            self, "Pipeline",
            synth=aws_cdk.pipelines.ShellStep(
                "Synth",
                input=aws_cdk.pipelines.CodePipelineSource.code_commit(repo, "main"),
                commands=[
                    "npm install -g aws-cdk",
                    "pip install -r requirements.txt",
                    "npx cdk synth",
                ]
            )
        )

        deploy = CdkPipelineStage(self, "Deploy")
        deploy_stage = pipeline.add_stage(deploy)
