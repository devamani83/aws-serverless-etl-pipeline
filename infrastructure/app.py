"""
AWS CDK Infrastructure for Advisory Performance ETL Pipeline
Deploys all necessary AWS resources for the serverless ETL solution
"""

from aws_cdk import (
    App,
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_glue as glue,
    aws_iam as iam,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
    aws_sns as sns,
    aws_events as events,
    aws_events_targets as targets,
    aws_cloudwatch as cloudwatch,
    aws_logs as logs,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_apigateway as apigateway,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    CfnOutput
)
from constructs import Construct
import json

class AdvisoryPerformanceETLStack(Stack):
    """Main CDK Stack for Advisory Performance ETL Pipeline"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create VPC for RDS
        self.vpc = self.create_vpc()
        
        # Create S3 buckets
        self.buckets = self.create_s3_buckets()
        
        # Create RDS PostgreSQL database
        self.database = self.create_database()
        
        # Create IAM roles
        self.roles = self.create_iam_roles()
        
        # Create Lambda functions
        self.lambda_functions = self.create_lambda_functions()
        
        # Create Glue jobs
        self.glue_jobs = self.create_glue_jobs()
        
        # Create Step Functions
        self.state_machine = self.create_step_functions()
        
        # Create SNS topics for notifications
        self.notification_topic = self.create_sns_topic()
        
        # Create frontend infrastructure
        self.frontend_infrastructure = self.create_frontend_infrastructure()
        
        # Create API Gateway for backend
        self.api_gateway = self.create_api_gateway()
        
        # Create S3 event triggers
        self.setup_s3_triggers()
        
        # Create CloudWatch monitoring
        self.create_monitoring()
        
        # Output important ARNs and endpoints
        self.create_outputs()
    
    def create_vpc(self):
        """Create VPC for RDS database"""
        vpc = ec2.Vpc(
            self, "AdvisoryETLVPC",
            max_azs=2,
            nat_gateways=1,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PUBLIC,
                    name="Public",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    name="Private",
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    name="Database",
                    cidr_mask=24
                )
            ]
        )
        return vpc
    
    def create_s3_buckets(self):
        """Create S3 buckets for data storage"""
        buckets = {}
        
        # Raw data bucket
        buckets['raw_data'] = s3.Bucket(
            self, "RawDataBucket",
            bucket_name="advisory-etl-raw-data",
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="archive-old-data",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ]
        )
        
        # Processed data bucket
        buckets['processed_data'] = s3.Bucket(
            self, "ProcessedDataBucket",
            bucket_name="advisory-etl-processed-data",
            versioned=True,
            removal_policy=RemovalPolicy.RETAIN
        )
        
        # Temporary data bucket
        buckets['temp'] = s3.Bucket(
            self, "TempDataBucket",
            bucket_name="advisory-etl-temp",
            removal_policy=RemovalPolicy.DESTROY,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="cleanup-temp-data",
                    expiration=Duration.days(7)
                )
            ]
        )
        
        # Archive bucket
        buckets['archive'] = s3.Bucket(
            self, "ArchiveBucket",
            bucket_name="advisory-etl-archive",
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="archive-lifecycle",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.DEEP_ARCHIVE,
                            transition_after=Duration.days(365)
                        )
                    ]
                )
            ]
        )
        
        # Config bucket for storing configurations
        buckets['config'] = s3.Bucket(
            self, "ConfigBucket",
            bucket_name="advisory-etl-config",
            removal_policy=RemovalPolicy.RETAIN,
            versioned=True
        )
        
        return buckets
    
    def create_database(self):
        """Create RDS PostgreSQL database"""
        # Create database security group
        db_security_group = ec2.SecurityGroup(
            self, "DatabaseSecurityGroup",
            vpc=self.vpc,
            description="Security group for Advisory Performance database",
            allow_all_outbound=False
        )
        
        # Allow inbound connections from Lambda and Glue
        db_security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL connections from VPC"
        )
        
        # Create database subnet group
        subnet_group = rds.SubnetGroup(
            self, "DatabaseSubnetGroup",
            description="Subnet group for Advisory Performance database",
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            )
        )
        
        # Create database secret
        db_secret = secretsmanager.Secret(
            self, "DatabaseSecret",
            secret_name="advisory-etl/db-password",
            description="Database password for Advisory Performance ETL",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps({"username": "etl_user"}),
                generate_string_key="password",
                exclude_characters='"@/\\\''
            )
        )
        
        # Create RDS instance
        database = rds.DatabaseInstance(
            self, "Database",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15_4
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.R5,
                ec2.InstanceSize.LARGE
            ),
            vpc=self.vpc,
            subnet_group=subnet_group,
            security_groups=[db_security_group],
            database_name="advisory_performance",
            credentials=rds.Credentials.from_secret(db_secret),
            allocated_storage=100,
            max_allocated_storage=1000,
            storage_type=rds.StorageType.GP2,
            backup_retention=Duration.days(7),
            delete_automated_backups=True,
            deletion_protection=True,
            enable_performance_insights=True,
            performance_insight_retention=rds.PerformanceInsightRetention.DEFAULT,
            monitoring_interval=Duration.seconds(60),
            removal_policy=RemovalPolicy.RETAIN
        )
        
        return {
            'instance': database,
            'secret': db_secret,
            'security_group': db_security_group
        }
    
    def create_iam_roles(self):
        """Create IAM roles for various services"""
        roles = {}
        
        # Glue service role
        roles['glue'] = iam.Role(
            self, "GlueServiceRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSGlueServiceRole")
            ],
            inline_policies={
                "S3Access": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                bucket.bucket_arn for bucket in self.buckets.values()
                            ] + [
                                f"{bucket.bucket_arn}/*" for bucket in self.buckets.values()
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue"
                            ],
                            resources=[self.database['secret'].secret_arn]
                        )
                    ]
                )
            }
        )
        
        # Lambda execution role
        roles['lambda'] = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")
            ],
            inline_policies={
                "ETLPermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:ListBucket"
                            ],
                            resources=[
                                bucket.bucket_arn for bucket in self.buckets.values()
                            ] + [
                                f"{bucket.bucket_arn}/*" for bucket in self.buckets.values()
                            ]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "glue:StartJobRun",
                                "glue:GetJobRun",
                                "glue:GetJobRuns"
                            ],
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "states:StartExecution"
                            ],
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue"
                            ],
                            resources=[self.database['secret'].secret_arn]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "sns:Publish"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        # Step Functions execution role
        roles['stepfunctions'] = iam.Role(
            self, "StepFunctionsExecutionRole",
            assumed_by=iam.ServicePrincipal("states.amazonaws.com"),
            inline_policies={
                "StepFunctionsPermissions": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "lambda:InvokeFunction"
                            ],
                            resources=["*"]
                        ),
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=[
                                "glue:StartJobRun",
                                "glue:GetJobRun",
                                "glue:BatchStopJobRun"
                            ],
                            resources=["*"]
                        )
                    ]
                )
            }
        )
        
        return roles
    
    def create_lambda_functions(self):
        """Create Lambda functions"""
        functions = {}
        
        # ETL Orchestrator Lambda
        functions['orchestrator'] = lambda_.Function(
            self, "ETLOrchestrator",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="etl_orchestrator.lambda_handler",
            code=lambda_.Code.from_asset("lambda-functions"),
            timeout=Duration.minutes(5),
            memory_size=512,
            role=self.roles['lambda'],
            environment={
                "GLUE_JOB_NAME": "advisory-performance-etl",
                "CONFIG_PATH": f"s3://{self.buckets['config'].bucket_name}/environment.json",
                "DB_HOST": self.database['instance'].instance_endpoint.hostname,
                "DB_PORT": str(self.database['instance'].instance_endpoint.port),
                "DB_NAME": "advisory_performance",
                "DB_USERNAME": "etl_user",
                "DB_PASSWORD_SECRET": self.database['secret'].secret_name
            },
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_groups=[self.database['security_group']]
        )
        
        # Reconciliation Engine Lambda
        functions['reconciliation'] = lambda_.Function(
            self, "ReconciliationEngine",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="reconciliation_engine.lambda_handler",
            code=lambda_.Code.from_asset("lambda-functions"),
            timeout=Duration.minutes(15),
            memory_size=1024,
            role=self.roles['lambda'],
            environment={
                "DB_HOST": self.database['instance'].instance_endpoint.hostname,
                "DB_PORT": str(self.database['instance'].instance_endpoint.port),
                "DB_NAME": "advisory_performance",
                "DB_USERNAME": "etl_user",
                "DB_PASSWORD_SECRET": self.database['secret'].secret_name
            },
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_groups=[self.database['security_group']],
            layers=[
                lambda_.LayerVersion(
                    self, "PsycopgLayer",
                    code=lambda_.Code.from_asset("layers/psycopg2"),
                    compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
                    description="Psycopg2 layer for PostgreSQL connectivity"
                )
            ]
        )
        
        return functions
    
    def create_glue_jobs(self):
        """Create AWS Glue jobs"""
        jobs = {}
        
        # Main ETL Job
        jobs['etl'] = glue.CfnJob(
            self, "MainETLJob",
            name="advisory-performance-etl",
            role=self.roles['glue'].role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{self.buckets['config'].bucket_name}/scripts/advisory_performance_etl.py"
            ),
            default_arguments={
                "--job-language": "python",
                "--job-bookmark-option": "job-bookmark-enable",
                "--enable-continuous-cloudwatch-log": "true",
                "--enable-metrics": "true",
                "--enable-spark-ui": "true",
                "--spark-event-logs-path": f"s3://{self.buckets['temp'].bucket_name}/spark-logs/",
                "--TempDir": f"s3://{self.buckets['temp'].bucket_name}/glue-temp/",
                "--additional-python-modules": "awswrangler==3.5.2,great-expectations==0.18.8"
            },
            max_capacity=10.0,
            timeout=2880,  # 48 hours
            max_retries=2,
            glue_version="4.0"
        )
        
        # Data Quality Checker Job
        jobs['data_quality'] = glue.CfnJob(
            self, "DataQualityJob",
            name="advisory-data-quality-checker",
            role=self.roles['glue'].role_arn,
            command=glue.CfnJob.JobCommandProperty(
                name="glueetl",
                python_version="3",
                script_location=f"s3://{self.buckets['config'].bucket_name}/scripts/data_quality_checker.py"
            ),
            default_arguments={
                "--job-language": "python",
                "--enable-continuous-cloudwatch-log": "true",
                "--TempDir": f"s3://{self.buckets['temp'].bucket_name}/glue-temp/"
            },
            max_capacity=5.0,
            timeout=1440,  # 24 hours
            glue_version="4.0"
        )
        
        return jobs
    
    def create_step_functions(self):
        """Create Step Functions state machine"""
        # Load the state machine definition
        with open('step-functions/etl_workflow.json', 'r') as f:
            definition = json.load(f)
        
        state_machine = sfn.StateMachine(
            self, "ETLWorkflow",
            state_machine_name="advisory-performance-etl-workflow",
            definition_body=sfn.DefinitionBody.from_string(json.dumps(definition)),
            role=self.roles['stepfunctions'],
            timeout=Duration.hours(4)
        )
        
        return state_machine
    
    def create_sns_topic(self):
        """Create SNS topic for notifications"""
        topic = sns.Topic(
            self, "ETLNotifications",
            topic_name="advisory-etl-notifications",
            display_name="Advisory Performance ETL Notifications"
        )
        
        return topic
    
    def setup_s3_triggers(self):
        """Setup S3 event triggers"""
        # Trigger Lambda on file upload to raw data bucket
        self.buckets['raw_data'].add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.lambda_functions['orchestrator']),
            s3.NotificationKeyFilter(
                prefix="incoming/",
                suffix=".csv"
            )
        )
        
        self.buckets['raw_data'].add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.lambda_functions['orchestrator']),
            s3.NotificationKeyFilter(
                prefix="incoming/",
                suffix=".json"
            )
        )
        
        self.buckets['raw_data'].add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.lambda_functions['orchestrator']),
            s3.NotificationKeyFilter(
                prefix="incoming/",
                suffix=".xlsx"
            )
        )
    
    def create_monitoring(self):
        """Create CloudWatch monitoring and alarms"""
        # Create log groups
        etl_log_group = logs.LogGroup(
            self, "ETLLogGroup",
            log_group_name="/aws/glue/advisory-performance-etl",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # Create CloudWatch dashboard
        dashboard = cloudwatch.Dashboard(
            self, "ETLDashboard",
            dashboard_name="AdvisoryPerformanceETL"
        )
        
        # Add widgets to dashboard
        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Glue Job Execution Status",
                left=[
                    cloudwatch.Metric(
                        namespace="AWS/Glue",
                        metric_name="glue.driver.aggregate.numCompletedTasks",
                        dimensions_map={"JobName": "advisory-performance-etl"}
                    )
                ]
            )
        )
        
        # Create alarms
        lambda_error_alarm = cloudwatch.Alarm(
            self, "LambdaErrorAlarm",
            metric=self.lambda_functions['orchestrator'].metric_errors(),
            threshold=1,
            evaluation_periods=1,
            alarm_description="Lambda function errors"
        )
        
        lambda_error_alarm.add_alarm_action(
            cloudwatch.SnsAction(self.notification_topic)
        )
    
    def create_outputs(self):
        """Create CloudFormation outputs"""
        CfnOutput(
            self, "DatabaseEndpoint",
            value=self.database['instance'].instance_endpoint.hostname,
            description="RDS PostgreSQL endpoint"
        )
        
        CfnOutput(
            self, "RawDataBucket",
            value=self.buckets['raw_data'].bucket_name,
            description="S3 bucket for raw data"
        )
        
        CfnOutput(
            self, "FrontendBucket",
            value=self.frontend_infrastructure['bucket'].bucket_name,
            description="S3 bucket for frontend application"
        )
        
        CfnOutput(
            self, "CloudFrontURL",
            value=f"https://{self.frontend_infrastructure['distribution'].distribution_domain_name}",
            description="CloudFront distribution URL for frontend"
        )
        
        CfnOutput(
            self, "APIGatewayURL",
            value=self.api_gateway['api'].url,
            description="API Gateway endpoint URL"
        )
        
        CfnOutput(
            self, "StepFunctionArn",
            value=self.state_machine.state_machine_arn,
            description="Step Functions state machine ARN"
        )
        
        CfnOutput(
            self, "NotificationTopicArn",
            value=self.notification_topic.topic_arn,
            description="SNS topic for notifications"
        )

    def create_frontend_infrastructure(self):
        """Create S3 bucket and CloudFront distribution for frontend"""
        # Frontend S3 bucket
        frontend_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name="advisory-etl-frontend",
            website_index_document="index.html",
            website_error_document="index.html",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )
        
        # Origin Access Identity for CloudFront
        origin_access_identity = cloudfront.OriginAccessIdentity(
            self, "FrontendOAI",
            comment="OAI for Advisory ETL Frontend"
        )
        
        # Grant CloudFront access to S3 bucket
        frontend_bucket.grant_read(origin_access_identity)
        
        # SSL Certificate (would need to be created in us-east-1 for CloudFront)
        # certificate = acm.Certificate(
        #     self, "FrontendCertificate",
        #     domain_name="app.advisory-etl.example.com",
        #     validation=acm.CertificateValidation.from_dns()
        # )
        
        # CloudFront distribution
        distribution = cloudfront.CloudFrontWebDistribution(
            self, "FrontendDistribution",
            origin_configs=[
                cloudfront.SourceConfiguration(
                    s3_origin_source=cloudfront.S3OriginConfig(
                        s3_bucket_source=frontend_bucket,
                        origin_access_identity=origin_access_identity
                    ),
                    behaviors=[
                        cloudfront.Behavior(
                            is_default_behavior=True,
                            viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                            compress=True,
                            cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED
                        )
                    ]
                )
            ],
            error_configurations=[
                cloudfront.CfnDistribution.CustomErrorResponseProperty(
                    error_code=404,
                    response_code=200,
                    response_page_path="/index.html"
                )
            ],
            comment="Advisory ETL Frontend Distribution",
            default_root_object="index.html"
        )
        
        return {
            'bucket': frontend_bucket,
            'distribution': distribution,
            'oai': origin_access_identity
        }
    
    def create_api_gateway(self):
        """Create API Gateway for backend services"""
        # Create API Gateway
        api = apigateway.RestApi(
            self, "AdvisoryETLAPI",
            rest_api_name="Advisory ETL API",
            description="REST API for Advisory ETL Pipeline",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"]
            )
        )
        
        # Create Lambda function for API backend
        api_lambda = lambda_.Function(
            self, "APIBackend",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("../ui-application/backend"),
            timeout=Duration.seconds(30),
            memory_size=512,
            environment={
                "DB_HOST": self.database['instance'].instance_endpoint.hostname,
                "DB_NAME": "advisory_performance",
                "DB_USERNAME": "postgres",
                "DB_PASSWORD_SECRET": self.database['secret'].secret_arn
            }
        )
        
        # Grant API Lambda access to database secret
        self.database['secret'].grant_read(api_lambda)
        
        # Grant API Lambda access to VPC (if database is in VPC)
        api_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface"
                ],
                resources=["*"]
            )
        )
        
        # Create API Gateway integration
        api_integration = apigateway.LambdaIntegration(
            api_lambda,
            request_templates={"application/json": '{ "statusCode": "200" }'}
        )
        
        # Add API routes
        api_resource = api.root.add_resource("api")
        
        # Health check endpoint
        health_resource = api_resource.add_resource("health")
        health_resource.add_method("GET", api_integration)
        
        # Vendors endpoint
        vendors_resource = api_resource.add_resource("vendors")
        vendors_resource.add_method("GET", api_integration)
        
        vendor_resource = vendors_resource.add_resource("{vendor}")
        files_resource = vendor_resource.add_resource("files")
        files_resource.add_method("GET", api_integration)
        
        # Files endpoint
        files_resource_root = api_resource.add_resource("files")
        file_resource = files_resource_root.add_resource("{file_id}")
        
        details_resource = file_resource.add_resource("details")
        details_resource.add_method("GET", api_integration)
        
        data_resource = file_resource.add_resource("data")
        data_resource.add_method("GET", api_integration)
        
        # Reconciliation endpoint
        reconciliation_resource = api_resource.add_resource("reconciliation")
        reconciliation_file_resource = reconciliation_resource.add_resource("{file_id}")
        reconciliation_file_resource.add_method("GET", api_integration)
        
        # Accounts endpoint
        accounts_resource = api_resource.add_resource("accounts")
        account_resource = accounts_resource.add_resource("{account_id}")
        account_resource.add_method("GET", api_integration)
        
        # Dashboard endpoint
        dashboard_resource = api_resource.add_resource("dashboard")
        summary_resource = dashboard_resource.add_resource("summary")
        summary_resource.add_method("GET", api_integration)
        
        # Quality endpoint
        quality_resource = api_resource.add_resource("quality")
        score_resource = quality_resource.add_resource("score")
        score_resource.add_method("GET", api_integration)
        
        return {
            'api': api,
            'lambda': api_lambda
        }

# CDK App
app = App()
AdvisoryPerformanceETLStack(app, "AdvisoryPerformanceETLStack")
app.synth()
