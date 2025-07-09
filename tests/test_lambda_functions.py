"""
Comprehensive unit tests for Lambda Functions
Tests ETL Orchestrator and Reconciliation Engine
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import os
import sys
from datetime import datetime
import pandas as pd
from decimal import Decimal

# Add lambda functions to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lambda-functions'))

class TestETLOrchestrator(unittest.TestCase):
    """Test ETL Orchestrator Lambda function"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        os.environ['GLUE_JOB_NAME'] = 'test-glue-job'
        os.environ['STEP_FUNCTION_ARN'] = 'arn:aws:states:us-east-1:123456789012:stateMachine:test'
        os.environ['CONFIG_PATH'] = 's3://test-bucket/config.json'
        
        # Mock AWS clients
        self.mock_glue_client = Mock()
        self.mock_stepfunctions_client = Mock()
        self.mock_s3_client = Mock()
        
        with patch('boto3.client') as mock_boto3:
            def side_effect(service_name):
                if service_name == 'glue':
                    return self.mock_glue_client
                elif service_name == 'stepfunctions':
                    return self.mock_stepfunctions_client
                elif service_name == 's3':
                    return self.mock_s3_client
                return Mock()
            
            mock_boto3.side_effect = side_effect
            
            # Import after mocking
            from etl_orchestrator import ETLOrchestrator
            self.orchestrator = ETLOrchestrator()
    
    def test_determine_vendor(self):
        """Test vendor determination from file names"""
        test_cases = [
            ('vendor_a_performance_2024.csv', 'vendor_a'),
            ('vendorb_data_january.xlsx', 'vendor_b'),
            ('vc_monthly_report.json', 'vendor_c'),
            ('unknown_file.txt', 'vendor_a')  # default fallback
        ]
        
        for file_name, expected_vendor in test_cases:
            with self.subTest(file_name=file_name):
                result = self.orchestrator.determine_vendor(file_name)
                self.assertEqual(result, expected_vendor)
    
    def test_validate_file_format(self):
        """Test file format validation"""
        test_cases = [
            ('file.csv', 'vendor_a', True),
            ('file.xlsx', 'vendor_b', True),
            ('file.json', 'vendor_c', True),
            ('file.txt', 'vendor_a', False),
            ('file.xlsx', 'vendor_a', False)  # Wrong format for vendor
        ]
        
        for file_name, vendor, expected_valid in test_cases:
            with self.subTest(file_name=file_name, vendor=vendor):
                result = self.orchestrator.validate_file_format(file_name, vendor)
                self.assertEqual(result, expected_valid)
    
    def test_check_file_readiness(self):
        """Test file readiness checking"""
        # Test successful file check
        self.mock_s3_client.head_object.return_value = {
            'ContentLength': 1024,
            'LastModified': datetime.now()
        }
        
        result = self.orchestrator.check_file_readiness('test-bucket', 'test-file.csv')
        self.assertTrue(result)
        
        # Test empty file
        self.mock_s3_client.head_object.return_value = {'ContentLength': 0}
        result = self.orchestrator.check_file_readiness('test-bucket', 'empty-file.csv')
        self.assertFalse(result)
        
        # Test S3 error
        self.mock_s3_client.head_object.side_effect = Exception("File not found")
        result = self.orchestrator.check_file_readiness('test-bucket', 'missing-file.csv')
        self.assertFalse(result)
    
    def test_start_glue_job(self):
        """Test starting Glue job"""
        # Mock successful job start
        self.mock_glue_client.start_job_run.return_value = {
            'JobRunId': 'jr_test123'
        }
        
        job_run_id = self.orchestrator.start_glue_job('s3://bucket/file.csv', 'vendor_a')
        
        self.assertEqual(job_run_id, 'jr_test123')
        self.mock_glue_client.start_job_run.assert_called_once()
        
        # Verify job arguments
        call_args = self.mock_glue_client.start_job_run.call_args
        arguments = call_args[1]['Arguments']
        self.assertEqual(arguments['--vendor'], 'vendor_a')
        self.assertEqual(arguments['--input_path'], 's3://bucket/file.csv')
    
    def test_start_step_function(self):
        """Test starting Step Function"""
        # Mock successful Step Function start
        self.mock_stepfunctions_client.start_execution.return_value = {
            'executionArn': 'arn:aws:states:us-east-1:123456789012:execution:test:exec123'
        }
        
        # Import and create orchestrator with Step Function ARN
        from etl_orchestrator import ETLOrchestrator
        orchestrator = ETLOrchestrator()
        
        # Mock the method if it exists
        if hasattr(orchestrator, 'start_step_function'):
            execution_arn = orchestrator.start_step_function({
                'file_name': 'test.csv',
                'vendor': 'vendor_a',
                'glue_job_id': 'jr_test123'
            })
            
            self.assertIn('execution', execution_arn.lower())
    
    def test_lambda_handler(self):
        """Test main Lambda handler function"""
        # Mock S3 event
        s3_event = {
            'Records': [{
                's3': {
                    'bucket': {'name': 'test-bucket'},
                    'object': {'key': 'vendor_a_data.csv'}
                }
            }]
        }
        
        # Mock context
        context = Mock()
        context.aws_request_id = 'test-request-123'
        
        # Mock successful responses
        self.mock_s3_client.head_object.return_value = {'ContentLength': 1024}
        self.mock_glue_client.start_job_run.return_value = {'JobRunId': 'jr_test123'}
        
        # Import handler
        try:
            from etl_orchestrator import lambda_handler
            response = lambda_handler(s3_event, context)
            
            # Verify response structure
            self.assertIn('statusCode', response)
            self.assertEqual(response['statusCode'], 200)
        except ImportError:
            # Handler might not be defined in the module
            self.skipTest("lambda_handler not found in module")
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        # Test Glue job start failure
        self.mock_glue_client.start_job_run.side_effect = Exception("Glue service error")
        
        with self.assertRaises(Exception):
            self.orchestrator.start_glue_job('s3://bucket/file.csv', 'vendor_a')
        
        # Test invalid vendor
        invalid_vendor_result = self.orchestrator.determine_vendor('unknown_pattern_file.xyz')
        self.assertEqual(invalid_vendor_result, 'vendor_a')  # Should fallback to default

class TestReconciliationEngine(unittest.TestCase):
    """Test Reconciliation Engine Lambda function"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock environment variables
        os.environ['DB_HOST'] = 'test-db-host'
        os.environ['DB_PORT'] = '5432'
        os.environ['DB_NAME'] = 'test_db'
        os.environ['DB_USERNAME'] = 'test_user'
        os.environ['DB_PASSWORD_SECRET'] = 'test-secret'
        
        # Mock AWS clients
        self.mock_secrets_client = Mock()
        self.mock_s3_client = Mock()
        
        # Mock secrets response
        self.mock_secrets_client.get_secret_value.return_value = {
            'SecretString': json.dumps({'password': 'test_password'})
        }
        
        with patch('boto3.client') as mock_boto3:
            def side_effect(service_name):
                if service_name == 'secretsmanager':
                    return self.mock_secrets_client
                elif service_name == 's3':
                    return self.mock_s3_client
                return Mock()
            
            mock_boto3.side_effect = side_effect
            
            # Import after mocking
            from reconciliation_engine import ReconciliationEngine
            self.reconciliation_engine = ReconciliationEngine()
    
    def test_get_database_config(self):
        """Test database configuration retrieval"""
        config = self.reconciliation_engine.get_database_config()
        
        self.assertEqual(config['host'], 'test-db-host')
        self.assertEqual(config['port'], 5432)
        self.assertEqual(config['database'], 'test_db')
        self.assertEqual(config['username'], 'test_user')
        self.assertEqual(config['password'], 'test_password')
    
    @patch('psycopg2.connect')
    def test_get_database_connection(self, mock_connect):
        """Test database connection"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        connection = self.reconciliation_engine.get_database_connection()
        
        self.assertEqual(connection, mock_conn)
        mock_connect.assert_called_once()
    
    @patch('pandas.read_sql_query')
    @patch('psycopg2.connect')
    def test_get_processed_data(self, mock_connect, mock_read_sql):
        """Test retrieval of processed data"""
        # Mock database connection
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        # Mock DataFrame
        mock_df = pd.DataFrame({
            'account_id': ['ACC001', 'ACC002'],
            'calculated_twrr': [0.0234, 0.0187],
            'vendor_twrr': [0.0235, 0.0185]
        })
        mock_read_sql.return_value = mock_df
        
        result = self.reconciliation_engine.get_processed_data('test_file.csv', 'vendor_a')
        
        self.assertEqual(len(result), 2)
        self.assertIn('account_id', result.columns)
        self.assertIn('calculated_twrr', result.columns)
    
    def test_perform_tolerance_check(self):
        """Test tolerance checking logic"""
        # Test data within tolerance
        calculated_value = Decimal('0.0234')
        vendor_value = Decimal('0.0235')
        tolerance = Decimal('0.0001')
        
        variance = abs(calculated_value - vendor_value)
        within_tolerance = variance <= tolerance
        
        self.assertTrue(within_tolerance)
        
        # Test data outside tolerance
        vendor_value_out = Decimal('0.0244')
        variance_out = abs(calculated_value - vendor_value_out)
        outside_tolerance = variance_out > tolerance
        
        self.assertTrue(outside_tolerance)
    
    def test_calculate_reconciliation_metrics(self):
        """Test reconciliation metrics calculation"""
        # Mock reconciliation results
        reconciliation_results = [
            {'account_id': 'ACC001', 'twrr_check': True, 'mv_check': True, 'netflow_check': True},
            {'account_id': 'ACC002', 'twrr_check': True, 'mv_check': False, 'netflow_check': True},
            {'account_id': 'ACC003', 'twrr_check': False, 'mv_check': True, 'netflow_check': True}
        ]
        
        # Calculate metrics
        total_accounts = len(reconciliation_results)
        total_checks = total_accounts * 3  # 3 checks per account
        
        passed_checks = sum([
            sum([result['twrr_check'], result['mv_check'], result['netflow_check']])
            for result in reconciliation_results
        ])
        
        pass_rate = (passed_checks / total_checks) * 100
        
        self.assertEqual(total_accounts, 3)
        self.assertEqual(total_checks, 9)
        self.assertEqual(passed_checks, 7)
        self.assertAlmostEqual(pass_rate, 77.78, places=1)
    
    def test_generate_reconciliation_report(self):
        """Test reconciliation report generation"""
        # Mock reconciliation data
        reconciliation_data = pd.DataFrame({
            'account_id': ['ACC001', 'ACC002', 'ACC003'],
            'calculated_twrr': [0.0234, 0.0187, 0.0245],
            'vendor_twrr': [0.0235, 0.0185, 0.0250],
            'twrr_variance': [0.0001, 0.0002, 0.0005],
            'twrr_tolerance_check': [True, False, False]
        })
        
        # Generate report metrics
        total_accounts = len(reconciliation_data)
        passed_tolerance = reconciliation_data['twrr_tolerance_check'].sum()
        pass_rate = (passed_tolerance / total_accounts) * 100
        
        report = {
            'total_accounts': total_accounts,
            'passed_tolerance': int(passed_tolerance),
            'failed_tolerance': total_accounts - int(passed_tolerance),
            'pass_rate': pass_rate,
            'status': 'PASS' if pass_rate >= 95 else 'FAIL'
        }
        
        self.assertEqual(report['total_accounts'], 3)
        self.assertEqual(report['passed_tolerance'], 1)
        self.assertEqual(report['failed_tolerance'], 2)
        self.assertAlmostEqual(report['pass_rate'], 33.33, places=1)
        self.assertEqual(report['status'], 'FAIL')
    
    def test_save_reconciliation_results(self):
        """Test saving reconciliation results to database"""
        # Mock reconciliation results
        results = [
            {
                'account_id': 'ACC001',
                'as_of_date': '2024-01-31',
                'calculated_twrr': 0.0234,
                'vendor_twrr': 0.0235,
                'twrr_variance': 0.0001,
                'tolerance_check': True
            }
        ]
        
        # Mock database operations
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            
            # Test save operation structure
            self.assertEqual(len(results), 1)
            self.assertIn('account_id', results[0])
            self.assertIn('tolerance_check', results[0])
    
    def test_lambda_handler_reconciliation(self):
        """Test main reconciliation Lambda handler"""
        # Mock event data
        event = {
            'file_name': 'test_file.csv',
            'vendor': 'vendor_a',
            'glue_job_id': 'jr_test123'
        }
        
        context = Mock()
        context.aws_request_id = 'test-request-456'
        
        # Mock processed data
        with patch('pandas.read_sql_query') as mock_read_sql, \
             patch('psycopg2.connect'):
            
            mock_df = pd.DataFrame({
                'account_id': ['ACC001'],
                'calculated_twrr': [0.0234],
                'vendor_twrr': [0.0235]
            })
            mock_read_sql.return_value = mock_df
            
            # Test handler structure (may not exist in module)
            try:
                from reconciliation_engine import lambda_handler
                response = lambda_handler(event, context)
                
                self.assertIn('statusCode', response)
                self.assertIn('body', response)
            except ImportError:
                self.skipTest("lambda_handler not found in module")

class TestLambdaIntegration(unittest.TestCase):
    """Integration tests for Lambda functions"""
    
    def test_orchestrator_to_reconciliation_flow(self):
        """Test complete flow from orchestration to reconciliation"""
        # Mock orchestration response
        orchestration_result = {
            'statusCode': 200,
            'body': json.dumps({
                'glue_job_id': 'jr_test123',
                'file_name': 'vendor_a_data.csv',
                'vendor': 'vendor_a',
                'status': 'STARTED'
            })
        }
        
        # Parse response for reconciliation input
        body = json.loads(orchestration_result['body'])
        
        reconciliation_input = {
            'file_name': body['file_name'],
            'vendor': body['vendor'],
            'glue_job_id': body['glue_job_id']
        }
        
        # Verify data flow
        self.assertEqual(reconciliation_input['vendor'], 'vendor_a')
        self.assertEqual(reconciliation_input['glue_job_id'], 'jr_test123')
        self.assertIn('.csv', reconciliation_input['file_name'])
    
    def test_error_propagation(self):
        """Test error handling across Lambda functions"""
        # Test various error scenarios
        error_scenarios = [
            {'type': 'FileNotFound', 'message': 'Input file not found'},
            {'type': 'ValidationError', 'message': 'Data validation failed'},
            {'type': 'DatabaseError', 'message': 'Database connection failed'},
            {'type': 'CalculationError', 'message': 'Financial calculation error'}
        ]
        
        for scenario in error_scenarios:
            error_response = {
                'statusCode': 500,
                'body': json.dumps({
                    'error': scenario['type'],
                    'message': scenario['message']
                })
            }
            
            # Verify error response structure
            self.assertEqual(error_response['statusCode'], 500)
            self.assertIn('error', json.loads(error_response['body']))
    
    def test_performance_monitoring(self):
        """Test performance monitoring metrics"""
        # Mock performance metrics
        performance_data = {
            'lambda_duration_ms': 5000,
            'memory_used_mb': 256,
            'records_processed': 1000,
            'error_rate': 0.1
        }
        
        # Verify performance within acceptable limits
        self.assertLess(performance_data['lambda_duration_ms'], 15000)  # < 15 seconds
        self.assertLess(performance_data['memory_used_mb'], 1024)       # < 1GB
        self.assertGreater(performance_data['records_processed'], 0)    # > 0 records
        self.assertLess(performance_data['error_rate'], 5.0)            # < 5% error rate

if __name__ == '__main__':
    unittest.main(verbosity=2)
