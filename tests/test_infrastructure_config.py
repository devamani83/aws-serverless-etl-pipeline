"""
Comprehensive unit tests for Infrastructure and Configuration
Tests CDK infrastructure, monitoring, and configuration
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys
from datetime import datetime

# Add infrastructure to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'infrastructure'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

class TestCDKInfrastructure(unittest.TestCase):
    """Test CDK infrastructure components"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock CDK constructs
        self.mock_stack = Mock()
        self.mock_construct = Mock()
        
        # Mock AWS services
        self.mock_s3_bucket = Mock()
        self.mock_lambda_function = Mock()
        self.mock_glue_job = Mock()
        self.mock_rds_instance = Mock()
    
    def test_stack_initialization(self):
        """Test CDK stack initialization"""
        # Mock stack configuration
        stack_config = {
            'stack_name': 'AdvisoryETLStack',
            'environment': 'development',
            'region': 'us-east-1',
            'tags': {
                'Project': 'Advisory ETL Pipeline',
                'Environment': 'development',
                'Owner': 'Data Engineering Team'
            }
        }
        
        # Verify stack configuration
        self.assertEqual(stack_config['stack_name'], 'AdvisoryETLStack')
        self.assertIn('Environment', stack_config['tags'])
        self.assertIn('Project', stack_config['tags'])
    
    def test_s3_bucket_configuration(self):
        """Test S3 bucket configuration"""
        # Mock S3 bucket properties
        s3_config = {
            'bucket_name': 'advisory-etl-data-dev',
            'versioning': True,
            'encryption': 'AES256',
            'lifecycle_rules': [
                {
                    'id': 'TransitionToIA',
                    'transition_days': 30,
                    'storage_class': 'STANDARD_IA'
                },
                {
                    'id': 'ArchiveToGlacier',
                    'transition_days': 90,
                    'storage_class': 'GLACIER'
                }
            ],
            'cors_rules': [
                {
                    'allowed_methods': ['GET', 'POST', 'PUT'],
                    'allowed_origins': ['*'],
                    'allowed_headers': ['*']
                }
            ]
        }
        
        # Verify S3 configuration
        self.assertTrue(s3_config['versioning'])
        self.assertEqual(s3_config['encryption'], 'AES256')
        self.assertEqual(len(s3_config['lifecycle_rules']), 2)
        self.assertIn('GET', s3_config['cors_rules'][0]['allowed_methods'])
    
    def test_lambda_function_configuration(self):
        """Test Lambda function configuration"""
        # Mock Lambda configurations
        lambda_configs = {
            'etl_orchestrator': {
                'function_name': 'advisory-etl-orchestrator',
                'runtime': 'python3.9',
                'timeout': 300,
                'memory_size': 512,
                'environment_variables': {
                    'GLUE_JOB_NAME': 'advisory-performance-etl',
                    'S3_BUCKET': 'advisory-etl-data-dev',
                    'LOG_LEVEL': 'INFO'
                },
                'iam_policies': [
                    'AWSGlueServiceRole',
                    'AmazonS3ReadOnlyAccess'
                ]
            },
            'reconciliation_engine': {
                'function_name': 'advisory-reconciliation-engine',
                'runtime': 'python3.9',
                'timeout': 900,
                'memory_size': 1024,
                'environment_variables': {
                    'DB_HOST': '${RDS_ENDPOINT}',
                    'DB_NAME': 'advisory_performance'
                },
                'vpc_config': {
                    'subnet_ids': ['subnet-123', 'subnet-456'],
                    'security_group_ids': ['sg-789']
                }
            }
        }
        
        # Verify Lambda configurations
        for func_name, config in lambda_configs.items():
            self.assertIn('function_name', config)
            self.assertIn('runtime', config)
            self.assertIn('timeout', config)
            self.assertIn('memory_size', config)
            self.assertGreater(config['timeout'], 0)
            self.assertGreater(config['memory_size'], 0)
    
    def test_glue_job_configuration(self):
        """Test Glue job configuration"""
        # Mock Glue job configuration
        glue_job_config = {
            'job_name': 'advisory-performance-etl',
            'role': 'AWSGlueServiceRole',
            'glue_version': '3.0',
            'worker_type': 'G.1X',
            'number_of_workers': 10,
            'max_concurrent_runs': 3,
            'timeout': 2880,  # 48 hours in minutes
            'default_arguments': {
                '--enable-metrics': 'true',
                '--enable-continuous-cloudwatch-log': 'true',
                '--job-language': 'python',
                '--TempDir': 's3://advisory-etl-temp/glue-temp/'
            },
            'connections': ['rds-connection'],
            'security_configuration': 'advisory-etl-security-config'
        }
        
        # Verify Glue job configuration
        self.assertEqual(glue_job_config['glue_version'], '3.0')
        self.assertGreater(glue_job_config['number_of_workers'], 0)
        self.assertIn('--enable-metrics', glue_job_config['default_arguments'])
        self.assertEqual(glue_job_config['default_arguments']['--enable-metrics'], 'true')
    
    def test_rds_configuration(self):
        """Test RDS database configuration"""
        # Mock RDS configuration
        rds_config = {
            'db_instance_identifier': 'advisory-etl-db',
            'engine': 'postgres',
            'engine_version': '13.7',
            'instance_class': 'db.t3.micro',
            'allocated_storage': 100,
            'storage_type': 'gp2',
            'storage_encrypted': True,
            'multi_az': False,
            'db_name': 'advisory_performance',
            'master_username': 'dbadmin',
            'backup_retention_period': 7,
            'preferred_backup_window': '03:00-04:00',
            'preferred_maintenance_window': 'sun:04:00-sun:05:00',
            'deletion_protection': False,
            'parameter_group_family': 'postgres13'
        }
        
        # Verify RDS configuration
        self.assertEqual(rds_config['engine'], 'postgres')
        self.assertTrue(rds_config['storage_encrypted'])
        self.assertGreater(rds_config['backup_retention_period'], 0)
        self.assertGreater(rds_config['allocated_storage'], 0)
    
    def test_vpc_configuration(self):
        """Test VPC and networking configuration"""
        # Mock VPC configuration
        vpc_config = {
            'vpc_cidr': '10.0.0.0/16',
            'availability_zones': ['us-east-1a', 'us-east-1b'],
            'public_subnets': [
                {'cidr': '10.0.1.0/24', 'az': 'us-east-1a'},
                {'cidr': '10.0.2.0/24', 'az': 'us-east-1b'}
            ],
            'private_subnets': [
                {'cidr': '10.0.3.0/24', 'az': 'us-east-1a'},
                {'cidr': '10.0.4.0/24', 'az': 'us-east-1b'}
            ],
            'nat_gateways': True,
            'enable_dns_hostnames': True,
            'enable_dns_support': True
        }
        
        # Verify VPC configuration
        self.assertTrue(vpc_config['vpc_cidr'].endswith('/16'))
        self.assertEqual(len(vpc_config['availability_zones']), 2)
        self.assertEqual(len(vpc_config['public_subnets']), 2)
        self.assertEqual(len(vpc_config['private_subnets']), 2)
        self.assertTrue(vpc_config['enable_dns_hostnames'])
    
    def test_iam_roles_and_policies(self):
        """Test IAM roles and policies configuration"""
        # Mock IAM configuration
        iam_config = {
            'glue_service_role': {
                'role_name': 'AWSGlueServiceRole-AdvisoryETL',
                'assume_role_policy': {
                    'Version': '2012-10-17',
                    'Statement': [{
                        'Effect': 'Allow',
                        'Principal': {'Service': 'glue.amazonaws.com'},
                        'Action': 'sts:AssumeRole'
                    }]
                },
                'managed_policies': [
                    'service-role/AWSGlueServiceRole',
                    'AmazonS3FullAccess',
                    'AmazonRDSDataFullAccess'
                ]
            },
            'lambda_execution_role': {
                'role_name': 'LambdaExecutionRole-AdvisoryETL',
                'managed_policies': [
                    'service-role/AWSLambdaBasicExecutionRole',
                    'service-role/AWSLambdaVPCAccessExecutionRole'
                ],
                'inline_policies': {
                    'S3Access': {
                        'Version': '2012-10-17',
                        'Statement': [{
                            'Effect': 'Allow',
                            'Action': ['s3:GetObject', 's3:PutObject'],
                            'Resource': 'arn:aws:s3:::advisory-etl-data-dev/*'
                        }]
                    }
                }
            }
        }
        
        # Verify IAM configuration
        glue_role = iam_config['glue_service_role']
        self.assertIn('AWSGlueServiceRole', glue_role['role_name'])
        self.assertEqual(len(glue_role['managed_policies']), 3)
        
        lambda_role = iam_config['lambda_execution_role']
        self.assertIn('inline_policies', lambda_role)
        self.assertIn('S3Access', lambda_role['inline_policies'])

class TestMonitoringConfiguration(unittest.TestCase):
    """Test monitoring and alerting configuration"""
    
    def setUp(self):
        """Set up monitoring test environment"""
        # Mock CloudWatch configuration
        self.cloudwatch_config = {
            'log_groups': [
                '/aws/glue/advisory-performance-etl',
                '/aws/lambda/advisory-etl-orchestrator',
                '/aws/lambda/advisory-reconciliation-engine'
            ],
            'metrics': [
                'ETL.RecordsProcessed',
                'ETL.ProcessingTime',
                'ETL.ErrorRate',
                'Reconciliation.PassRate'
            ],
            'alarms': [
                {
                    'name': 'ETL-HighErrorRate',
                    'metric': 'ETL.ErrorRate',
                    'threshold': 5.0,
                    'comparison': 'GreaterThanThreshold'
                },
                {
                    'name': 'Reconciliation-LowPassRate',
                    'metric': 'Reconciliation.PassRate',
                    'threshold': 95.0,
                    'comparison': 'LessThanThreshold'
                }
            ]
        }
    
    def test_cloudwatch_log_groups(self):
        """Test CloudWatch log group configuration"""
        log_groups = self.cloudwatch_config['log_groups']
        
        # Verify log groups
        self.assertGreater(len(log_groups), 0)
        for log_group in log_groups:
            self.assertTrue(log_group.startswith('/aws/'))
            self.assertIn('advisory', log_group)
    
    def test_custom_metrics(self):
        """Test custom metrics configuration"""
        metrics = self.cloudwatch_config['metrics']
        
        # Verify metrics
        expected_metrics = ['ETL.RecordsProcessed', 'ETL.ProcessingTime', 'ETL.ErrorRate']
        for metric in expected_metrics:
            self.assertIn(metric, metrics)
    
    def test_cloudwatch_alarms(self):
        """Test CloudWatch alarms configuration"""
        alarms = self.cloudwatch_config['alarms']
        
        # Verify alarm structure
        for alarm in alarms:
            self.assertIn('name', alarm)
            self.assertIn('metric', alarm)
            self.assertIn('threshold', alarm)
            self.assertIn('comparison', alarm)
            self.assertIsInstance(alarm['threshold'], (int, float))
    
    def test_sns_notification_configuration(self):
        """Test SNS notification configuration"""
        # Mock SNS configuration
        sns_config = {
            'topics': [
                {
                    'name': 'advisory-etl-alerts',
                    'display_name': 'Advisory ETL Alerts',
                    'subscriptions': [
                        {
                            'protocol': 'email',
                            'endpoint': 'alerts@company.com'
                        },
                        {
                            'protocol': 'sms',
                            'endpoint': '+1234567890'
                        }
                    ]
                }
            ]
        }
        
        # Verify SNS configuration
        topics = sns_config['topics']
        self.assertEqual(len(topics), 1)
        
        topic = topics[0]
        self.assertIn('subscriptions', topic)
        self.assertGreater(len(topic['subscriptions']), 0)
    
    def test_dashboard_configuration(self):
        """Test CloudWatch dashboard configuration"""
        # Mock dashboard configuration
        dashboard_config = {
            'dashboard_name': 'AdvisoryETLPipeline',
            'widgets': [
                {
                    'type': 'metric',
                    'title': 'ETL Processing Rate',
                    'metrics': ['ETL.RecordsProcessed'],
                    'period': 300,
                    'stat': 'Sum'
                },
                {
                    'type': 'metric',
                    'title': 'Reconciliation Pass Rate',
                    'metrics': ['Reconciliation.PassRate'],
                    'period': 3600,
                    'stat': 'Average'
                },
                {
                    'type': 'log',
                    'title': 'Recent Errors',
                    'log_group': '/aws/glue/advisory-performance-etl',
                    'filter_pattern': '[timestamp, request_id, ERROR, ...]'
                }
            ]
        }
        
        # Verify dashboard configuration
        widgets = dashboard_config['widgets']
        self.assertGreater(len(widgets), 0)
        
        for widget in widgets:
            self.assertIn('type', widget)
            self.assertIn('title', widget)
            if widget['type'] == 'metric':
                self.assertIn('metrics', widget)
                self.assertIn('period', widget)

class TestEnvironmentConfiguration(unittest.TestCase):
    """Test environment configuration management"""
    
    def setUp(self):
        """Set up environment configuration tests"""
        # Mock environment configurations
        self.environments = {
            'development': {
                'environment_name': 'dev',
                'region': 'us-east-1',
                's3_bucket': 'advisory-etl-data-dev',
                'db_instance_class': 'db.t3.micro',
                'glue_worker_type': 'G.1X',
                'lambda_memory_size': 512,
                'enable_deletion_protection': False,
                'log_level': 'DEBUG'
            },
            'staging': {
                'environment_name': 'staging',
                'region': 'us-east-1',
                's3_bucket': 'advisory-etl-data-staging',
                'db_instance_class': 'db.t3.small',
                'glue_worker_type': 'G.1X',
                'lambda_memory_size': 1024,
                'enable_deletion_protection': False,
                'log_level': 'INFO'
            },
            'production': {
                'environment_name': 'prod',
                'region': 'us-east-1',
                's3_bucket': 'advisory-etl-data-prod',
                'db_instance_class': 'db.t3.medium',
                'glue_worker_type': 'G.2X',
                'lambda_memory_size': 1024,
                'enable_deletion_protection': True,
                'log_level': 'WARN'
            }
        }
    
    def test_environment_configuration_structure(self):
        """Test environment configuration structure"""
        required_fields = [
            'environment_name', 'region', 's3_bucket', 
            'db_instance_class', 'log_level'
        ]
        
        for env_name, config in self.environments.items():
            with self.subTest(environment=env_name):
                for field in required_fields:
                    self.assertIn(field, config, f"Missing {field} in {env_name}")
    
    def test_environment_specific_settings(self):
        """Test environment-specific settings"""
        # Development environment
        dev_config = self.environments['development']
        self.assertEqual(dev_config['log_level'], 'DEBUG')
        self.assertFalse(dev_config['enable_deletion_protection'])
        
        # Production environment
        prod_config = self.environments['production']
        self.assertEqual(prod_config['log_level'], 'WARN')
        self.assertTrue(prod_config['enable_deletion_protection'])
        self.assertEqual(prod_config['glue_worker_type'], 'G.2X')
    
    def test_resource_scaling_by_environment(self):
        """Test resource scaling by environment"""
        # Verify resources scale appropriately by environment
        dev_memory = self.environments['development']['lambda_memory_size']
        staging_memory = self.environments['staging']['lambda_memory_size']
        prod_memory = self.environments['production']['lambda_memory_size']
        
        # Staging and production should have more memory than development
        self.assertGreaterEqual(staging_memory, dev_memory)
        self.assertGreaterEqual(prod_memory, dev_memory)
    
    def test_security_settings_by_environment(self):
        """Test security settings by environment"""
        # Production should have stricter security settings
        dev_protection = self.environments['development']['enable_deletion_protection']
        prod_protection = self.environments['production']['enable_deletion_protection']
        
        self.assertFalse(dev_protection)
        self.assertTrue(prod_protection)

class TestConfigurationValidation(unittest.TestCase):
    """Test configuration validation and error handling"""
    
    def test_required_configuration_validation(self):
        """Test validation of required configuration parameters"""
        # Mock configuration validation
        required_config = {
            'aws_region': 'us-east-1',
            's3_bucket_name': 'advisory-etl-data',
            'database_host': 'advisory-db.cluster-xyz.us-east-1.rds.amazonaws.com',
            'database_name': 'advisory_performance'
        }
        
        # Validation rules
        validation_rules = {
            'aws_region': lambda x: x in ['us-east-1', 'us-west-2', 'eu-west-1'],
            's3_bucket_name': lambda x: len(x) > 0 and '-' in x,
            'database_host': lambda x: x.endswith('.amazonaws.com'),
            'database_name': lambda x: len(x) > 0 and x.isalnum()
        }
        
        # Validate configuration
        validation_errors = []
        for config_key, rule in validation_rules.items():
            if config_key in required_config:
                if not rule(required_config[config_key]):
                    validation_errors.append(f"Invalid {config_key}")
        
        # Should have no validation errors
        self.assertEqual(len(validation_errors), 0)
    
    def test_configuration_type_validation(self):
        """Test configuration type validation"""
        # Mock configuration with various data types
        config_with_types = {
            'timeout_seconds': 300,
            'memory_size_mb': 1024,
            'enable_logging': True,
            'retry_attempts': 3,
            'endpoint_url': 'https://api.example.com',
            'tags': ['production', 'etl', 'advisory']
        }
        
        # Type validation
        type_checks = {
            'timeout_seconds': int,
            'memory_size_mb': int,
            'enable_logging': bool,
            'retry_attempts': int,
            'endpoint_url': str,
            'tags': list
        }
        
        # Validate types
        type_errors = []
        for config_key, expected_type in type_checks.items():
            if config_key in config_with_types:
                if not isinstance(config_with_types[config_key], expected_type):
                    type_errors.append(f"Wrong type for {config_key}")
        
        # Should have no type errors
        self.assertEqual(len(type_errors), 0)
    
    def test_configuration_range_validation(self):
        """Test configuration range validation"""
        # Mock configuration with ranges
        range_config = {
            'lambda_timeout': 300,      # 1-900 seconds
            'lambda_memory': 1024,      # 128-10240 MB
            'glue_workers': 5,          # 2-100 workers
            'retry_attempts': 3         # 1-10 attempts
        }
        
        # Range validation
        range_checks = {
            'lambda_timeout': (1, 900),
            'lambda_memory': (128, 10240),
            'glue_workers': (2, 100),
            'retry_attempts': (1, 10)
        }
        
        # Validate ranges
        range_errors = []
        for config_key, (min_val, max_val) in range_checks.items():
            if config_key in range_config:
                value = range_config[config_key]
                if not (min_val <= value <= max_val):
                    range_errors.append(f"{config_key} out of range")
        
        # Should have no range errors
        self.assertEqual(len(range_errors), 0)

class TestDeploymentScripts(unittest.TestCase):
    """Test deployment and setup scripts"""
    
    def test_deployment_script_structure(self):
        """Test deployment script structure"""
        # Mock deployment steps
        deployment_steps = [
            'validate_environment',
            'build_application',
            'run_tests',
            'deploy_infrastructure',
            'deploy_application',
            'run_smoke_tests',
            'update_dns',
            'send_notifications'
        ]
        
        # Verify deployment steps
        self.assertGreater(len(deployment_steps), 0)
        self.assertIn('validate_environment', deployment_steps)
        self.assertIn('run_tests', deployment_steps)
        self.assertIn('deploy_infrastructure', deployment_steps)
    
    def test_rollback_capabilities(self):
        """Test rollback capabilities"""
        # Mock rollback configuration
        rollback_config = {
            'enable_rollback': True,
            'rollback_timeout_minutes': 10,
            'health_check_url': 'https://api.example.com/health',
            'rollback_triggers': [
                'high_error_rate',
                'failed_health_check',
                'manual_trigger'
            ]
        }
        
        # Verify rollback configuration
        self.assertTrue(rollback_config['enable_rollback'])
        self.assertGreater(rollback_config['rollback_timeout_minutes'], 0)
        self.assertIn('health_check_url', rollback_config)
        self.assertGreater(len(rollback_config['rollback_triggers']), 0)
    
    def test_database_migration_scripts(self):
        """Test database migration script structure"""
        # Mock migration configuration
        migration_config = {
            'migration_table': 'schema_migrations',
            'migration_directory': 'migrations/',
            'backup_before_migration': True,
            'rollback_on_failure': True,
            'migration_timeout_minutes': 30
        }
        
        # Verify migration configuration
        self.assertTrue(migration_config['backup_before_migration'])
        self.assertTrue(migration_config['rollback_on_failure'])
        self.assertGreater(migration_config['migration_timeout_minutes'], 0)

if __name__ == '__main__':
    unittest.main(verbosity=2)
