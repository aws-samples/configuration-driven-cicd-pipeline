# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from aws_cdk import Stage
from constructs import Construct

from dynamic_pipeline.dynamic_pipeline_stack import DynamicPipelineStack


class CdkPipelineStage(Stage):

    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        service = DynamicPipelineStack(self, 'BaseStack')
