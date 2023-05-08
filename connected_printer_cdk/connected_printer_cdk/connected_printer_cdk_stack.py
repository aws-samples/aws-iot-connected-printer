# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_iam as _iam,
    aws_dynamodb as _dynamodb,
    aws_s3 as _s3,
    aws_s3_deployment as _s3_deployment,
    aws_s3_notifications as _s3_notify,
    aws_apigateway as _apigw,
    aws_iot_alpha as _iot,
    aws_iot as _iot_core,
    aws_iot_actions_alpha as _actions,
    aws_cognito as _cognito,
    aws_logs as _logs,
    Aspects
)
import aws_cdk as _cdk_core
import cdk_nag


class ConnectedPrinterCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## userpool for api access
        api_userpool = _cognito.UserPool(
            self, "APIPool",
            advanced_security_mode=_cognito.AdvancedSecurityMode.ENFORCED,
            password_policy=_cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_digits=True,
                require_symbols=True,
                require_uppercase=True
            )
        )

        ## api pool client for registration
        api_pool_client = api_userpool.add_client("app-client")

        ## authentication authorizor for apiGW
        api_auth = _apigw.CognitoUserPoolsAuthorizer(
            self, 'api_authorizor',
            cognito_user_pools=[api_userpool]
        )

        ## output the ARN of our cognito client_id for user sign up
        _cdk_core.CfnOutput(
            self, 'cognito_userpool_client_id',
            value=api_userpool.user_pool_id
        )

        ## output the ARN of our cognito client_id for user sign up
        _cdk_core.CfnOutput(
            self, 'cognito_app_client_id',
            value=api_pool_client.user_pool_client_id
        )

        ## Execution Role for LambdaFN
        lambda_exec_role = _iam.Role(
            scope=self, 
            id='cdk-lambda-role',
            assumed_by =_iam.ServicePrincipal('lambda.amazonaws.com'),
            role_name='cdk-lambda-role'
        )

        ## Dynamo DB Table used for capturing device attributes and customer associations
        device_telemetry_table = _dynamodb.Table(
            self, 'device_telemetry_data',
            partition_key={
                'name': 'sample_time',
                'type': _dynamodb.AttributeType.STRING
            },
            sort_key={
                'name': 'device_id',
                'type': _dynamodb.AttributeType.STRING
            },
            time_to_live_attribute="ttl",
            removal_policy=_cdk_core.RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        ## Dynamo DB Table used for capturing device readiness data
        device_inventory_table = _dynamodb.Table(
            self, 'device_inventory_table',
            partition_key={
                'name': 'device_id',
                'type': _dynamodb.AttributeType.STRING
            },
            removal_policy=_cdk_core.RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        ## Dynamo DB Table used for capturing Print Jobs in Detail, including Job Status, # Attempts, S3 Location
        job_status_table = _dynamodb.Table(
            self, 'job_status_table',
            partition_key={
                'name': 'job_id',
                'type': _dynamodb.AttributeType.STRING
            },
            removal_policy=_cdk_core.RemovalPolicy.DESTROY,
            point_in_time_recovery=True
        )

        access_logs_bucket = _s3.Bucket(
            self, 'access_logs_bucket',
            removal_policy=_cdk_core.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True
        )

        ## S3 Bucket for storing Print Jobs & Card Designs
        print_job_bucket = _s3.Bucket(
            self, 'print_job_storage',
            removal_policy=_cdk_core.RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            block_public_access=_s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            server_access_logs_bucket=access_logs_bucket
        )

        print_job_bucket.server_access_logs_bucket = print_job_bucket
        print_job_bucket.server_access_logs_prefix = 'bucket_access_logs/'


        ## S3 Deployment; Uploads local Card Design images to S3
        card_designs_to_s3 = _s3_deployment.BucketDeployment(
            self, 'deploy_card_designs_to_s3',
            sources=[_s3_deployment.Source.asset('./s3')],
            destination_bucket=print_job_bucket,
            destination_key_prefix='card_designs/'
        )

        ## LambdaFN for writing print job presigned url to mqtt with iot core
        provisioning_lambda = _lambda.Function(
            self, 'device_provisioning_hook',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('lambda_device_provisioning_hook'),
            handler='device_provisioning_hook.lambda_handler',
            role=lambda_exec_role,
            timeout=Duration.seconds(30),
            environment={
                'DEVICE_INVENTORY_TABLE': device_inventory_table.table_name,
                'JOB_STATUS_TABLE': job_status_table.table_name,
                'PRINT_JOB_BUCKET': print_job_bucket.bucket_name
            }
        )

        ## output the ARN of our PreProvisioningHook Lambda FN
        _cdk_core.CfnOutput(
            self, 'provisioning_hook_lambda_arn',
            value=provisioning_lambda.function_arn
        )

        ## this allows IoT to call the provisioning hook Lambda FN
        _lambda.CfnPermission(
            self, "AllowIoTInvocation",
            action="lambda:InvokeFunction",
            function_name=provisioning_lambda.function_name,
            principal='iot.amazonaws.com'
        )

        ## creates a lambda layer for pillow, a package which enables png modification in our lambda function
        pillow_lambda_layer = _lambda.LayerVersion(
            self, 'pillow',
            code = _lambda.AssetCode('lambda_layer/layer/'),
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_8, 
                _lambda.Runtime.PYTHON_3_9
            ]
        )

        ## LambdaFN for capturing Print Jobs created in our front end, 
        # modifying card design png with cardholder name; 
        # stores in s3, creates print job record in ddb
        write_print_job = _lambda.Function(
            self, 'write_print_job',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('lambda_write_print_job'),
            handler='write_print_job.lambda_handler',
            role=lambda_exec_role,
            timeout=Duration.seconds(30),
            layers=[pillow_lambda_layer],
            environment={
                'DEVICE_INVENTORY_TABLE': device_inventory_table.table_name,
                'JOB_STATUS_TABLE': job_status_table.table_name,
                'PRINT_JOB_BUCKET': print_job_bucket.bucket_name
            }
        )

        ## LambdaFN  writing print job presigned url to mqtt with iot core
        process_print_job_mqtt = _lambda.Function(
            self, 'process_print_job_mqtt',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('lambda_process_print_job_mqtt'),
            handler='process_print_job_mqtt.lambda_handler',
            role=lambda_exec_role,
            timeout=Duration.seconds(30),
            environment={
                'DEVICE_INVENTORY_TABLE': device_inventory_table.table_name,
                'JOB_STATUS_TABLE': job_status_table.table_name,
                'PRINT_JOB_BUCKET': print_job_bucket.bucket_name
            }
        )

        ## Triggers the ProcessPrintJobMQTT Lambda when a print job file is created in S3
        print_job_bucket.add_event_notification(_s3.EventType.OBJECT_CREATED, _s3_notify.LambdaDestination(process_print_job_mqtt))

        ## LambdaFN for informing front end of customers/devices
        get_customers_devices = _lambda.Function(
            self, 'get_customers_devices',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('lambda_get_customers_devices'),
            handler='get_customers_devices.lambda_handler',
            role=lambda_exec_role,
            timeout=Duration.seconds(30),
            environment={
                'DEVICE_INVENTORY_TABLE': device_inventory_table.table_name,
                'JOB_STATUS_TABLE': job_status_table.table_name,
                'PRINT_JOB_BUCKET': print_job_bucket.bucket_name,
                'DEVICE_TELEMETRY_DATA': device_telemetry_table.table_name
            }
        )

        ## LambdaFN for updating job status records
        update_job_status = _lambda.Function(
            self, 'update_job_status',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('lambda_update_job_status'),
            handler='update_job_status.lambda_handler',
            role=lambda_exec_role,
            timeout=Duration.seconds(30),
            environment={
                'DEVICE_INVENTORY_TABLE': device_inventory_table.table_name,
                'JOB_STATUS_TABLE': job_status_table.table_name,
                'PRINT_JOB_BUCKET': print_job_bucket.bucket_name,
                'DEVICE_TELEMETRY_DATA': device_telemetry_table.table_name
            }
        )

        ## LambdaFN for getting job status records
        get_job_status = _lambda.Function(
            self, 'get_print_job_status',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('lambda_get_print_job_status'),
            handler='get_print_job_status.lambda_handler',
            role=lambda_exec_role,
            timeout=Duration.seconds(30),
            environment={
                'DEVICE_INVENTORY_TABLE': device_inventory_table.table_name,
                'JOB_STATUS_TABLE': job_status_table.table_name,
                'PRINT_JOB_BUCKET': print_job_bucket.bucket_name,
                'DEVICE_TELEMETRY_DATA': device_telemetry_table.table_name
            }
        )

        ## IoT Rule for Capturing Device Telemetry Data and writing to DynamoDB
        # TODO -- create IoT rule for capturing job status messages and triggering lambda
        job_status_rule = _iot.TopicRule(self, "job_status_rule",
            sql=_iot.IotSql.from_string_as_ver20160323("SELECT * FROM 'job_status/+/+'"),
            actions=[
                _actions.LambdaFunctionAction(update_job_status)
            ]
        )


        ## IAM Role for IoT Rule
        rule_exec_role = _iam.Role(
            scope=self, 
            id='rule-exec-role',
            assumed_by =_iam.ServicePrincipal('iot.amazonaws.com'),
            role_name='rule-exec-role'
        )

        rule_exec_role.add_to_policy(_iam.PolicyStatement(
            resources=[
                '*'
            ],
            actions=[
                'iot:Publish',
                'iot:Receive'
            ]
        ))

        rule_exec_role.add_to_policy(_iam.PolicyStatement(
            resources=[
                '*'
            ],
            actions=[
                'cloudwatch:*',
                'logs:*'
            ]
        ))

        rule_exec_role.add_to_policy(_iam.PolicyStatement(
            resources=[ 
                device_telemetry_table.table_arn,
                device_inventory_table.table_arn,
                job_status_table.table_arn
            ],
            actions=[
                'dynamodb:GetItem',
                'dynamodb:GetRecords',
                'dynamodb:ListTables',
                'dynamodb:PutItem',
                'dynamodb:Query',
                'dynamodb:Scan',
                'dynamodb:UpdateItem'
            ]
        ))

        ## IoT Rule for Capturing Device Telemetry Data and writing to DynamoDB
        device_telemetry_rule = _iot.TopicRule(self, "device_telemetry_rule",
            sql=_iot.IotSql.from_string_as_ver20160323("SELECT * FROM 'printer_status/+'"),
            actions=[
                _actions.DynamoDBv2PutItemAction(device_telemetry_table)
            ]
        )

        ## Lambda function for front end, checks telemetry_table and returns most recent status of a device
        device_availability_lambda = _lambda.Function(self, 'device_availability',
                                        handler='device_availability.lambda_handler',
                                        runtime=_lambda.Runtime.PYTHON_3_9,
                                        code=_lambda.Code.from_asset('lambda_device_availability'),
                                        role=lambda_exec_role,
                                        timeout=Duration.seconds(30),
                                        environment={
                                            'DEVICE_INVENTORY_TABLE': device_inventory_table.table_name,
                                            'JOB_STATUS_TABLE': job_status_table.table_name,
                                            'PRINT_JOB_BUCKET': print_job_bucket.bucket_name,
                                            'DEVICE_TELEMETRY_DATA': device_telemetry_table.table_name
                                        }
        )


        # access_log_group = _logs.LogGroup(self, "ConnectedPrinterLogGroup", retention=_logs.RetentionDays.ONE_MONTH)

        ## base API for post requests from front end
        front_end_api = _apigw.RestApi(
            self, 'connected_printer_api',
            rest_api_name='connected_printer_api'
        )

        # ## enable access logging on apigw
        # _stage: _apigw.CfnStage = front_end_api.default_stage.node.default_child
        # _stage.access_log_settings = _apigw.CfnStage.AccessLogSettingProperty(
        #     destination_arn=access_log_group.log_group_arn,
        #     format="$context.requiestId"
        # )

        api_validator = _apigw.RequestValidator(
            self, "feValidator",
            rest_api=front_end_api,
            validate_request_body=True,
            validate_request_parameters=True
            )
        
        ## this adds /printers onto the api and enables cors
        printers_api_resource = front_end_api.root.add_resource(
            'printers',
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_methods=['GET', 'OPTIONS', 'POST'],
                allow_origins=_apigw.Cors.ALL_ORIGINS)
        )

        ## this makes the resource integrate with our device_availability_lambda
        printers_api_lambda_integration = _apigw.LambdaIntegration(
            get_customers_devices,
            proxy=False,
            integration_responses=[
                _apigw.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    }
                )
            ]
        )

        ## this adds a POST method on our resource
        printers_api_resource.add_method(
            'GET', printers_api_lambda_integration,
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    }
                )
            ],
            authorizer=api_auth,
            authorization_type=_apigw.AuthorizationType.COGNITO
        )

        ## this adds /availability onto the api and enables cors
        api_availability_resource = front_end_api.root.add_resource(
            'availability',
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_methods=['GET', 'OPTIONS', 'POST'],
                allow_origins=_apigw.Cors.ALL_ORIGINS)
        )

        ## this makes the resource integrate with our device_availability_lambda
        device_availability_lambda_integration = _apigw.LambdaIntegration(
            device_availability_lambda,
            proxy=False,
            integration_responses=[
                _apigw.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    }
                )
            ]
        )

        ## this adds a POST method on our resource
        api_availability_resource.add_method(
            'POST', device_availability_lambda_integration,
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    }
                )
            ],
            authorizer=api_auth,
            authorization_type=_apigw.AuthorizationType.COGNITO
        )

        ## this adds /print onto the api and enables cors
        api_print_resource = front_end_api.root.add_resource(
            'print',
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_methods=['GET', 'OPTIONS', 'POST'],
                allow_origins=_apigw.Cors.ALL_ORIGINS)
        )

        ## this makes the resource integrate with our write_print_job lambda
        write_print_job_lambda_integration = _apigw.LambdaIntegration(
            write_print_job,
            proxy=False,
            integration_responses=[
                _apigw.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    }
                )
            ]
        )

        ## this adds a POST method on our resource
        api_print_resource.add_method(
            'POST', write_print_job_lambda_integration,
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    }
                )
            ],
            authorizer=api_auth,
            authorization_type=_apigw.AuthorizationType.COGNITO
        )

        ## this adds /print onto the api and enables cors
        api_print_status_resource = front_end_api.root.add_resource(
            'print_status',
            default_cors_preflight_options=_apigw.CorsOptions(
                allow_methods=['GET', 'OPTIONS', 'POST'],
                allow_origins=_apigw.Cors.ALL_ORIGINS)
        )

        ## this makes the resource integrate with our write_print_job lambda
        get_print_job_status_lambda_integration = _apigw.LambdaIntegration(
            get_job_status,
            proxy=False,
            integration_responses=[
                _apigw.IntegrationResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    }
                )
            ]
        )

        ## this adds a POST method on our resource
        api_print_status_resource.add_method(
            'POST', get_print_job_status_lambda_integration,
            method_responses=[
                _apigw.MethodResponse(
                    status_code="200",
                    response_parameters={
                        'method.response.header.Access-Control-Allow-Origin': True
                    }
                )
            ],
            authorizer=api_auth,
            authorization_type=_apigw.AuthorizationType.COGNITO
        )


        ## this adds a provisioning role
        provisioning_role = _iam.Role(
            scope=self, 
            id='IoTFleetProvisioningRole',
            assumed_by =_iam.ServicePrincipal('iot.amazonaws.com'),
            role_name='IoTFleetProvisioningRole',
            # inline_policies=['{"Version":"2012-10-17","Statement":[{"Action":"sts:AssumeRole","Effect":"Allow","Principal":{"Service":"iot.amazonaws.com"}}]}'],
            managed_policies= [
                _iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSIoTThingsRegistration')
            ]
        )

        ## this adds the provisioning template that we'll use to register our devices as printers
        provisioning_template = _iot_core.CfnProvisioningTemplate(
            self, "ConnectedPrinterTemplate",
            provisioning_role_arn=provisioning_role.role_arn,
            template_body='{ "Parameters": { "Customer": { "Type": "String" }, "AWS::IoT::Certificate::Id": { "Type": "String" }, "DeviceName": { "Type": "String" }, "DeviceID": { "Type": "String" }, "Location": { "Type": "String" } }, "Mappings": { "CustomerTable": { "MBAWS": { "CustomerUrl": "https://example.aws" } } }, "Resources": { "thing": { "Type": "AWS::IoT::Thing", "Properties": { "ThingName": { "Fn::Join": [ "", [ "Printer_", { "Ref": "DeviceID" } ] ] }, "AttributePayload": { "version": "v1", "deviceID": "deviceID" } }, "OverrideSettings": { "AttributePayload": "MERGE", "ThingTypeName": "REPLACE", "ThingGroups": "DO_NOTHING" } }, "certificate": { "Type": "AWS::IoT::Certificate", "Properties": { "CertificateId": { "Ref": "AWS::IoT::Certificate::Id" }, "Status": "Active" }, "OverrideSettings": { "Status": "REPLACE" } }, "policy": { "Type": "AWS::IoT::Policy", "Properties": { "PolicyDocument": { "Version": "2012-10-17", "Statement": [ { "Effect": "Allow", "Action": [ "iot:Connect", "iot:Subscribe", "iot:Publish", "iot:Receive" ], "Resource": "*" } ] } } } } }',
            enabled=True,
            pre_provisioning_hook=_iot_core.CfnProvisioningTemplate.ProvisioningHookProperty(
                payload_version="2020-04-01",
                target_arn=provisioning_lambda.function_arn
            ),
            template_name="ConnectedPrinterTemplate",
        )

        ## output the ARN of our PreProvisioningHook Lambda FN
        _cdk_core.CfnOutput(
            self, 'provisioning_template_name',
            value=provisioning_template.template_name
        )

        lambda_exec_role.add_to_policy(_iam.PolicyStatement(
            resources=[
                print_job_bucket.bucket_arn,
                f'${print_job_bucket.bucket_arn}/*'
            ],
            actions=[
                's3:PutObject',
                's3:GetObject',
                's3:ListBucket'
            ]
        ))

        lambda_exec_role.add_to_policy(_iam.PolicyStatement(
            resources=[
                '*'
            ],
            actions=[
                'iot:Publish',
                'iot:Receive'
            ]
        ))

        lambda_exec_role.add_to_policy(_iam.PolicyStatement(
            resources=[
                '*'
            ],
            actions=[
                'cloudwatch:*',
                'logs:*'
            ]
        ))

        lambda_exec_role.add_to_policy(_iam.PolicyStatement(
            resources=[ 
                device_telemetry_table.table_arn,
                device_inventory_table.table_arn,
                job_status_table.table_arn
            ],
            actions=[
                'dynamodb:GetItem',
                'dynamodb:GetRecords',
                'dynamodb:ListTables',
                'dynamodb:PutItem',
                'dynamodb:Query',
                'dynamodb:Scan',
                'dynamodb:UpdateItem'
            ]
        ))

        _NagSuppressions = cdk_nag.NagSuppressions()

        _NagSuppressions.add_resource_suppressions(
            lambda_exec_role,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "For S3, the wildcard applies to all objects within the bucket created specifically for this use case. For CloudWatch, wildcard permissions allows the role to create and write to function specific streams. The role is used by numerous Lambda Functions in this deployment."
                }
            ],
            apply_to_children=True
        )

        _NagSuppressions.add_resource_suppressions(
            rule_exec_role,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "Wildcard S3 permissions allows the rule to act on any object that is put to the bucket. This is a requirement."
                }
            ],
            apply_to_children=True
        )

        _NagSuppressions.add_resource_suppressions(
            access_logs_bucket,
            suppressions=[
                {
                    "id": "AwsSolutions-S1",
                    "reason": "This bucket is the bucket used to store server access logs for the other bucket in the deployment package."
                }
            ],
            apply_to_children=True
        )

        _NagSuppressions.add_resource_suppressions(
            provisioning_role,
            suppressions=[
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "This role is used for provisioning IoT devices. While the AWS-Managed policy it uses does not restrict resource scope, this solution is intended for learning purposes and not production workloads."
                }
            ],
            apply_to_children=True
        )

        _NagSuppressions.add_resource_suppressions(
            front_end_api,
            suppressions=[
                {
                    "id": "AwsSolutions-APIG6",
                    "reason": "Figure out how to enable cloudwatch logging for all methods."
                },
                {
                    "id": "AwsSolutions-APIG1",
                    "reason": "The RestApi construct in the aws-apigateway module does not offer visibility into default stage which prevents me from enabling access logging. Using aws-apigatewayv2 results in automatic break of the deployment package, as it does not currently support CognitoUserPoolsAuthorizer."
                }
            ],
            apply_to_children=True
        )

        _NagSuppressions.add_resource_suppressions(
            front_end_api,
            suppressions=[
                {
                    "id": "AwsSolutions-APIG4",
                    "reason": "All remaining methods which do not have logging enabled are OPTIONS methods."
                },
                {
                    "id": "AwsSolutions-COG4",
                    "reason": "All remaining methods which do not have logging enabled are OPTIONS methods."
                }
            ],
            apply_to_children=True
        )

        _NagSuppressions.add_resource_suppressions_by_path(
            self,
            '/connected-printer-cdk/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/ServiceRole/Resource', 
            suppressions=[
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "The upload objects to bucket resource automatically uses AWS-Managed Policies. Unless modified, the deployment will only upload the objects specified therein.",
                    "appliesTo": ['Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole']
                }
            ],
            apply_to_children=True
        )

        _NagSuppressions.add_resource_suppressions_by_path(
            self,
            '/connected-printer-cdk/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/ServiceRole/DefaultPolicy/Resource', 
            suppressions=[
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "The upload objects to bucket resource automatically uses wildcard permissiveness for uploading objects. Unless modified, the deployment will only upload the objects specified therein.",
                    "appliesTo": [
                        'Action::s3:GetBucket*',
                        'Action::s3:GetObject*',
                        'Action::s3:List*',
                        'Resource::arn:<AWS::Partition>:s3:::cdk-hnb659fds-assets-<AWS::AccountId>-<AWS::Region>/*',
                        'Action::s3:Abort*',
                        'Action::s3:DeleteObject*',
                        'Resource::<printjobstorage52930C08.Arn>/*'
                    ]
                }
            ],
            apply_to_children=True
        )

        _NagSuppressions.add_resource_suppressions_by_path(
            self,
            '/connected-printer-cdk/BucketNotificationsHandler050a0587b7544547bf325f094a3db834/Role/Resource',
            suppressions=[
                {
                    "id": "AwsSolutions-IAM4",
                    "reason": "The s3 notifications resource automatically uses AWS-Managed Policies.",
                    "appliesTo": ['Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole']
                },
                {
                    "id": "AwsSolutions-IAM5",
                    "reason": "The s3 notifications resource automatically uses wildcard permissiveness for uploading objects.",
                    "appliesTo": [
                        'Resource::*'
                    ]
                }
            ],
            apply_to_children=True
        )
        

        Aspects.of(self).add(cdk_nag.AwsSolutionsChecks(verbose=True))
        