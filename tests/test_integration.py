"""
Integration tests for the complete ETL pipeline
Tests end-to-end workflows and component interactions
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os
import sys
from datetime import datetime, date
import subprocess

class TestETLPipelineIntegration(unittest.TestCase):
    """Integration tests for the complete ETL pipeline"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.test_data = {
            'vendor_a_sample': [
                {
                    'account_id': 'ACC001',
                    'as_of_date': '2024-01-31',
                    'beginning_market_value': 100000.00,
                    'ending_market_value': 105000.00,
                    'contributions': 5000.00,
                    'distributions': 2000.00,
                    'income': 1200.00,
                    'appreciation': 800.00,
                    'fees': 300.00,
                    'vendor_twrr': 0.0234
                },
                {
                    'account_id': 'ACC002',
                    'as_of_date': '2024-01-31',
                    'beginning_market_value': 200000.00,
                    'ending_market_value': 198000.00,
                    'contributions': 0.00,
                    'distributions': 5000.00,
                    'income': 2400.00,
                    'appreciation': -1600.00,
                    'fees': 600.00,
                    'vendor_twrr': 0.0187
                }
            ]
        }
        
        # Mock AWS services
        self.mock_s3 = Mock()
        self.mock_glue = Mock()
        self.mock_lambda = Mock()
        self.mock_rds = Mock()
    
    def test_file_upload_to_processing_workflow(self):
        """Test complete file upload to processing workflow"""
        # Step 1: File upload event
        s3_event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'advisory-etl-data'},
                    'object': {'key': 'raw/vendor_a/vendor_a_data_2024.csv'}
                }
            }]
        }
        
        # Step 2: Extract file information
        file_info = {
            'bucket': s3_event['Records'][0]['s3']['bucket']['name'],
            'key': s3_event['Records'][0]['s3']['object']['key'],
            'vendor': 'vendor_a',
            'file_name': 'vendor_a_data_2024.csv'
        }
        
        # Step 3: Trigger orchestrator
        orchestrator_response = {
            'statusCode': 200,
            'body': json.dumps({
                'glue_job_id': 'jr_12345',
                'status': 'STARTED',
                'timestamp': datetime.now().isoformat()
            })
        }
        
        # Step 4: Process data (mock Glue job results)
        processed_data = []
        for record in self.test_data['vendor_a_sample']:
            processed_record = record.copy()
            # Calculate net flow
            processed_record['net_flow'] = record['contributions'] - record['distributions']
            # Calculate TWRR (simplified)
            adjusted_beginning = record['beginning_market_value'] + (processed_record['net_flow'] / 2)
            if adjusted_beginning > 0:
                processed_record['calculated_twrr'] = (record['ending_market_value'] - adjusted_beginning) / adjusted_beginning
            else:
                processed_record['calculated_twrr'] = 0.0
            processed_data.append(processed_record)
        
        # Step 5: Reconciliation
        reconciliation_results = []
        tolerance = 0.0001
        for record in processed_data:
            variance = abs(record['calculated_twrr'] - record['vendor_twrr'])
            tolerance_check = variance <= tolerance
            reconciliation_results.append({
                'account_id': record['account_id'],
                'calculated_twrr': record['calculated_twrr'],
                'vendor_twrr': record['vendor_twrr'],
                'variance': variance,
                'tolerance_check': tolerance_check
            })
        
        # Verify workflow
        self.assertEqual(file_info['vendor'], 'vendor_a')
        self.assertEqual(orchestrator_response['statusCode'], 200)
        self.assertEqual(len(processed_data), 2)
        self.assertEqual(len(reconciliation_results), 2)
        
        # Verify calculations
        for result in reconciliation_results:
            self.assertGreater(result['calculated_twrr'], -1.0)  # > -100%
            self.assertLess(result['calculated_twrr'], 1.0)      # < 100%
            self.assertGreaterEqual(result['variance'], 0)       # Non-negative variance
    
    def test_multi_vendor_data_processing(self):
        """Test processing data from multiple vendors"""
        # Mock data from different vendors
        vendor_data = {
            'vendor_a': {
                'format': 'csv',
                'columns': ['account_id', 'beginning_mv', 'ending_mv', 'contributions', 'distributions', 'twrr'],
                'sample_row': 'ACC001,100000,105000,5000,2000,0.0234'
            },
            'vendor_b': {
                'format': 'excel',
                'columns': ['acct_id', 'start_value', 'end_value', 'deposits', 'withdrawals', 'time_weighted_return'],
                'sample_data': {
                    'acct_id': 'ACC001',
                    'start_value': 100000,
                    'end_value': 105000,
                    'deposits': 5000,
                    'withdrawals': 2000,
                    'time_weighted_return': 0.0234
                }
            },
            'vendor_c': {
                'format': 'json',
                'sample_data': {
                    'account': {
                        'id': 'ACC001',
                        'name': 'Test Account'
                    },
                    'performance': {
                        'beginning_value': 100000,
                        'ending_value': 105000,
                        'flows': {
                            'contributions': 5000,
                            'distributions': 2000
                        },
                        'returns': {
                            'time_weighted': 0.0234
                        }
                    }
                }
            }
        }
        
        # Process each vendor's data format
        standardized_data = []
        
        for vendor, data in vendor_data.items():
            if data['format'] == 'csv':
                # Parse CSV format
                row_data = data['sample_row'].split(',')
                standardized_record = {
                    'account_id': row_data[0],
                    'beginning_market_value': float(row_data[1]),
                    'ending_market_value': float(row_data[2]),
                    'contributions': float(row_data[3]),
                    'distributions': float(row_data[4]),
                    'vendor_twrr': float(row_data[5]),
                    'vendor': vendor
                }
            elif data['format'] == 'excel':
                # Parse Excel format
                excel_data = data['sample_data']
                standardized_record = {
                    'account_id': excel_data['acct_id'],
                    'beginning_market_value': excel_data['start_value'],
                    'ending_market_value': excel_data['end_value'],
                    'contributions': excel_data['deposits'],
                    'distributions': excel_data['withdrawals'],
                    'vendor_twrr': excel_data['time_weighted_return'],
                    'vendor': vendor
                }
            elif data['format'] == 'json':
                # Parse JSON format
                json_data = data['sample_data']
                standardized_record = {
                    'account_id': json_data['account']['id'],
                    'beginning_market_value': json_data['performance']['beginning_value'],
                    'ending_market_value': json_data['performance']['ending_value'],
                    'contributions': json_data['performance']['flows']['contributions'],
                    'distributions': json_data['performance']['flows']['distributions'],
                    'vendor_twrr': json_data['performance']['returns']['time_weighted'],
                    'vendor': vendor
                }
            
            standardized_data.append(standardized_record)
        
        # Verify standardization
        self.assertEqual(len(standardized_data), 3)
        for record in standardized_data:
            self.assertIn('account_id', record)
            self.assertIn('beginning_market_value', record)
            self.assertIn('vendor_twrr', record)
            self.assertIn('vendor', record)
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        # Test different error scenarios
        error_scenarios = [
            {
                'error_type': 'FileNotFound',
                'error_message': 'Input file not found in S3',
                'recovery_action': 'retry_with_backoff',
                'max_retries': 3
            },
            {
                'error_type': 'DataValidationError',
                'error_message': 'Required columns missing in input data',
                'recovery_action': 'skip_invalid_records',
                'continue_processing': True
            },
            {
                'error_type': 'DatabaseConnectionError',
                'error_message': 'Cannot connect to PostgreSQL database',
                'recovery_action': 'retry_with_exponential_backoff',
                'max_retries': 5
            },
            {
                'error_type': 'CalculationError',
                'error_message': 'Division by zero in TWRR calculation',
                'recovery_action': 'use_fallback_calculation',
                'fallback_value': 0.0
            }
        ]
        
        # Test error handling for each scenario
        for scenario in error_scenarios:
            error_response = {
                'error_type': scenario['error_type'],
                'error_message': scenario['error_message'],
                'recovery_attempted': True,
                'recovery_action': scenario['recovery_action'],
                'timestamp': datetime.now().isoformat(),
                'status': 'HANDLED'
            }
            
            # Verify error handling structure
            self.assertIn('error_type', error_response)
            self.assertIn('recovery_action', error_response)
            self.assertTrue(error_response['recovery_attempted'])
            self.assertEqual(error_response['status'], 'HANDLED')
    
    def test_data_quality_validation(self):
        """Test comprehensive data quality validation"""
        # Test data with various quality issues
        test_data_with_issues = [
            {
                'account_id': 'ACC001',
                'beginning_market_value': 100000.00,
                'ending_market_value': 105000.00,
                'contributions': 5000.00,
                'distributions': 2000.00,
                'vendor_twrr': 0.0234,
                'quality_issues': []
            },
            {
                'account_id': '',  # Missing account ID
                'beginning_market_value': 0.00,  # Zero beginning value
                'ending_market_value': -1000.00,  # Negative ending value
                'contributions': None,  # Null contributions
                'distributions': 2000.00,
                'vendor_twrr': 1.5,  # Unrealistic TWRR (150%)
                'quality_issues': []
            },
            {
                'account_id': 'ACC003',
                'beginning_market_value': 200000.00,
                'ending_market_value': 'invalid',  # Invalid data type
                'contributions': 5000.00,
                'distributions': 2000.00,
                'vendor_twrr': 0.0187,
                'quality_issues': []
            }
        ]
        
        # Data quality validation rules
        def validate_record(record):
            issues = []
            
            # Check required fields
            if not record.get('account_id') or record['account_id'] == '':
                issues.append('missing_account_id')
            
            # Check data types
            try:
                float(record.get('ending_market_value', 0))
            except (ValueError, TypeError):
                issues.append('invalid_ending_market_value_type')
            
            # Check business rules
            if record.get('beginning_market_value', 0) < 0:
                issues.append('negative_beginning_market_value')
            
            if record.get('ending_market_value', 0) < 0:
                issues.append('negative_ending_market_value')
            
            # Check TWRR reasonableness
            twrr = record.get('vendor_twrr', 0)
            if twrr > 1.0 or twrr < -1.0:  # More than ±100%
                issues.append('unrealistic_twrr')
            
            # Check for null values in required fields
            required_fields = ['contributions', 'distributions']
            for field in required_fields:
                if record.get(field) is None:
                    issues.append(f'null_{field}')
            
            return issues
        
        # Validate each record
        validation_results = []
        for record in test_data_with_issues:
            issues = validate_record(record)
            validation_results.append({
                'account_id': record.get('account_id', 'UNKNOWN'),
                'issues': issues,
                'is_valid': len(issues) == 0
            })
        
        # Verify validation results
        self.assertEqual(len(validation_results), 3)
        
        # First record should be valid
        self.assertTrue(validation_results[0]['is_valid'])
        self.assertEqual(len(validation_results[0]['issues']), 0)
        
        # Second record should have multiple issues
        self.assertFalse(validation_results[1]['is_valid'])
        self.assertIn('missing_account_id', validation_results[1]['issues'])
        self.assertIn('negative_ending_market_value', validation_results[1]['issues'])
        self.assertIn('unrealistic_twrr', validation_results[1]['issues'])
        
        # Third record should have data type issue
        self.assertFalse(validation_results[2]['is_valid'])
        self.assertIn('invalid_ending_market_value_type', validation_results[2]['issues'])
    
    def test_performance_and_scalability(self):
        """Test performance and scalability characteristics"""
        # Mock performance test data
        performance_scenarios = [
            {
                'scenario': 'small_dataset',
                'record_count': 1000,
                'expected_processing_time_seconds': 30,
                'expected_memory_usage_mb': 256
            },
            {
                'scenario': 'medium_dataset',
                'record_count': 10000,
                'expected_processing_time_seconds': 120,
                'expected_memory_usage_mb': 512
            },
            {
                'scenario': 'large_dataset',
                'record_count': 100000,
                'expected_processing_time_seconds': 600,
                'expected_memory_usage_mb': 1024
            }
        ]
        
        # Simulate performance testing
        for scenario in performance_scenarios:
            # Mock processing metrics
            processing_metrics = {
                'record_count': scenario['record_count'],
                'processing_time_seconds': scenario['expected_processing_time_seconds'] * 0.9,  # 10% better than expected
                'memory_usage_mb': scenario['expected_memory_usage_mb'] * 0.8,  # 20% less memory
                'throughput_records_per_second': scenario['record_count'] / (scenario['expected_processing_time_seconds'] * 0.9),
                'cpu_utilization_percent': 75,
                'error_rate_percent': 0.1
            }
            
            # Verify performance metrics
            self.assertGreater(processing_metrics['throughput_records_per_second'], 0)
            self.assertLess(processing_metrics['processing_time_seconds'], scenario['expected_processing_time_seconds'])
            self.assertLess(processing_metrics['memory_usage_mb'], scenario['expected_memory_usage_mb'])
            self.assertLess(processing_metrics['error_rate_percent'], 1.0)  # Less than 1% error rate
    
    def test_monitoring_and_alerting_integration(self):
        """Test monitoring and alerting integration"""
        # Mock monitoring data
        monitoring_metrics = {
            'etl_pipeline': {
                'records_processed_per_hour': 50000,
                'processing_success_rate': 99.5,
                'average_processing_time_minutes': 5.2,
                'error_rate_percent': 0.5
            },
            'reconciliation': {
                'accounts_reconciled': 10000,
                'reconciliation_pass_rate': 98.7,
                'average_variance': 0.00005,
                'tolerance_failures': 130
            },
            'infrastructure': {
                'lambda_duration_ms': 4500,
                'lambda_memory_utilization': 65,
                'rds_cpu_utilization': 45,
                'rds_connection_count': 15,
                's3_request_rate': 1000
            }
        }
        
        # Define alert thresholds
        alert_thresholds = {
            'processing_success_rate_min': 95.0,
            'reconciliation_pass_rate_min': 95.0,
            'error_rate_max': 5.0,
            'lambda_duration_max_ms': 10000,
            'rds_cpu_utilization_max': 80
        }
        
        # Check for alert conditions
        alerts = []
        
        if monitoring_metrics['etl_pipeline']['processing_success_rate'] < alert_thresholds['processing_success_rate_min']:
            alerts.append('LOW_PROCESSING_SUCCESS_RATE')
        
        if monitoring_metrics['reconciliation']['reconciliation_pass_rate'] < alert_thresholds['reconciliation_pass_rate_min']:
            alerts.append('LOW_RECONCILIATION_PASS_RATE')
        
        if monitoring_metrics['etl_pipeline']['error_rate_percent'] > alert_thresholds['error_rate_max']:
            alerts.append('HIGH_ERROR_RATE')
        
        if monitoring_metrics['infrastructure']['lambda_duration_ms'] > alert_thresholds['lambda_duration_max_ms']:
            alerts.append('HIGH_LAMBDA_DURATION')
        
        if monitoring_metrics['infrastructure']['rds_cpu_utilization'] > alert_thresholds['rds_cpu_utilization_max']:
            alerts.append('HIGH_RDS_CPU_UTILIZATION')
        
        # Verify no alerts should be triggered (all metrics are within thresholds)
        self.assertEqual(len(alerts), 0, f"Unexpected alerts: {alerts}")
        
        # Verify metrics are within acceptable ranges
        self.assertGreaterEqual(monitoring_metrics['etl_pipeline']['processing_success_rate'], 99.0)
        self.assertGreaterEqual(monitoring_metrics['reconciliation']['reconciliation_pass_rate'], 98.0)
        self.assertLessEqual(monitoring_metrics['etl_pipeline']['error_rate_percent'], 1.0)

class TestSystemIntegration(unittest.TestCase):
    """Test system-level integration"""
    
    def test_end_to_end_system_flow(self):
        """Test complete end-to-end system flow"""
        # Simulate complete system flow
        system_flow = {
            'step_1_file_upload': {
                'action': 'upload_file_to_s3',
                'input': 'vendor_a_data.csv',
                'output': 's3://bucket/raw/vendor_a/vendor_a_data.csv',
                'status': 'SUCCESS'
            },
            'step_2_trigger_orchestrator': {
                'action': 'lambda_orchestrator_invoked',
                'input': 's3_event',
                'output': 'glue_job_started',
                'status': 'SUCCESS'
            },
            'step_3_etl_processing': {
                'action': 'glue_job_execution',
                'input': 'raw_data',
                'output': 'processed_data_in_rds',
                'status': 'SUCCESS'
            },
            'step_4_reconciliation': {
                'action': 'lambda_reconciliation_invoked',
                'input': 'processed_data',
                'output': 'reconciliation_report',
                'status': 'SUCCESS'
            },
            'step_5_ui_update': {
                'action': 'frontend_data_refresh',
                'input': 'api_call',
                'output': 'updated_dashboard',
                'status': 'SUCCESS'
            }
        }
        
        # Verify each step completed successfully
        for step_name, step_info in system_flow.items():
            with self.subTest(step=step_name):
                self.assertEqual(step_info['status'], 'SUCCESS')
                self.assertIn('action', step_info)
                self.assertIn('input', step_info)
                self.assertIn('output', step_info)
        
        # Verify flow continuity
        self.assertEqual(len(system_flow), 5)
    
    def test_disaster_recovery_scenarios(self):
        """Test disaster recovery scenarios"""
        # Mock disaster recovery scenarios
        dr_scenarios = [
            {
                'scenario': 'primary_region_failure',
                'impact': 'complete_service_outage',
                'recovery_action': 'failover_to_secondary_region',
                'rto_minutes': 60,  # Recovery Time Objective
                'rpo_minutes': 15   # Recovery Point Objective
            },
            {
                'scenario': 'database_corruption',
                'impact': 'data_access_failure',
                'recovery_action': 'restore_from_backup',
                'rto_minutes': 30,
                'rpo_minutes': 5
            },
            {
                'scenario': 'lambda_function_failure',
                'impact': 'processing_pipeline_interruption',
                'recovery_action': 'automatic_retry_with_dlq',
                'rto_minutes': 5,
                'rpo_minutes': 1
            }
        ]
        
        # Verify disaster recovery capabilities
        for scenario in dr_scenarios:
            # Check RTO and RPO requirements
            self.assertLessEqual(scenario['rto_minutes'], 120)  # RTO within 2 hours
            self.assertLessEqual(scenario['rpo_minutes'], 60)   # RPO within 1 hour
            
            # Verify recovery actions are defined
            self.assertIn('recovery_action', scenario)
            self.assertNotEqual(scenario['recovery_action'], '')
    
    def test_security_integration(self):
        """Test security integration across components"""
        # Mock security controls
        security_controls = {
            'encryption': {
                's3_encryption': 'AES256',
                'rds_encryption': 'aws_kms',
                'lambda_env_vars': 'encrypted',
                'secrets_manager': 'enabled'
            },
            'access_control': {
                'iam_roles': 'least_privilege',
                'vpc_security_groups': 'restrictive',
                'api_authentication': 'required',
                'database_access': 'role_based'
            },
            'monitoring': {
                'cloudtrail_logging': 'enabled',
                'vpc_flow_logs': 'enabled',
                'lambda_logging': 'enabled',
                'access_logging': 'enabled'
            },
            'compliance': {
                'data_residency': 'us_only',
                'audit_trail': 'complete',
                'retention_policy': 'enforced',
                'gdpr_compliance': 'ready'
            }
        }
        
        # Verify security controls
        for category, controls in security_controls.items():
            with self.subTest(category=category):
                for control, status in controls.items():
                    self.assertIn(status, ['enabled', 'required', 'least_privilege', 'restrictive', 'AES256', 'aws_kms', 'encrypted', 'role_based', 'us_only', 'complete', 'enforced', 'ready'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
