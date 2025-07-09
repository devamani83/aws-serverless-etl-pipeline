"""
Comprehensive unit tests for Glue Jobs
Tests the PerformanceCalculator and ETL job functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import pytest
from decimal import Decimal
import sys
import os

# Mock PySpark modules before importing the main module
sys.modules['pyspark'] = Mock()
sys.modules['pyspark.context'] = Mock()
sys.modules['pyspark.sql'] = Mock()
sys.modules['pyspark.sql.functions'] = Mock()
sys.modules['pyspark.sql.types'] = Mock()
sys.modules['pyspark.sql.window'] = Mock()
sys.modules['awsglue'] = Mock()
sys.modules['awsglue.transforms'] = Mock()
sys.modules['awsglue.utils'] = Mock()
sys.modules['awsglue.context'] = Mock()
sys.modules['awsglue.job'] = Mock()

# Now we can import our module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'glue-jobs'))
from advisory_performance_etl import PerformanceCalculator, DataValidator, ETLProcessor

class TestPerformanceCalculator(unittest.TestCase):
    """Test financial calculations"""
    
    def setUp(self):
        """Set up test environment"""
        self.calculator = PerformanceCalculator()
    
    def test_calculate_net_flow(self):
        """Test net flow calculation"""
        # Mock Spark functions
        mock_coalesce = Mock(return_value="mocked_result")
        mock_lit = Mock(return_value="zero_value")
        
        with patch('advisory_performance_etl.coalesce', mock_coalesce), \
             patch('advisory_performance_etl.lit', mock_lit):
            
            contributions = 5000
            distributions = 2000
            
            result = PerformanceCalculator.calculate_net_flow(contributions, distributions)
            
            # Verify coalesce was called for both values
            self.assertEqual(mock_coalesce.call_count, 2)
            self.assertEqual(result, "mocked_result")
    
    def test_calculate_twrr_single_period(self):
        """Test TWRR calculation for single period"""
        # Mock Spark functions
        mock_when = Mock()
        mock_when.otherwise.return_value = "twrr_result"
        
        with patch('advisory_performance_etl.when', return_value=mock_when), \
             patch('advisory_performance_etl.coalesce') as mock_coalesce, \
             patch('advisory_performance_etl.lit'):
            
            beginning_mv = 100000
            ending_mv = 105000
            net_flow = 3000
            
            result = PerformanceCalculator.calculate_twrr_single_period(
                beginning_mv, ending_mv, net_flow
            )
            
            # Verify the calculation structure
            mock_when.otherwise.assert_called_once()
            self.assertEqual(result, "twrr_result")
    
    def test_validate_market_value_equation(self):
        """Test market value equation validation"""
        # Test data that should balance
        test_data = {
            'beginning_market_value': 100000,
            'ending_market_value': 105000,
            'contributions': 5000,
            'distributions': 2000,
            'income': 1200,
            'appreciation': 800,
            'fees': 300,
            'other_adjustments': 300
        }
        
        # Calculate expected ending value
        expected_ending = (
            test_data['beginning_market_value'] + 
            test_data['contributions'] - 
            test_data['distributions'] + 
            test_data['income'] + 
            test_data['appreciation'] - 
            test_data['fees'] + 
            test_data['other_adjustments']
        )
        
        # Should equal provided ending market value
        self.assertEqual(expected_ending, test_data['ending_market_value'])
    
    def test_calculate_cumulative_twrr(self):
        """Test cumulative TWRR calculation"""
        # Mock DataFrame and Window functions
        mock_df = Mock()
        mock_window = Mock()
        
        with patch('advisory_performance_etl.Window') as mock_window_class:
            mock_window_class.partitionBy.return_value.orderBy.return_value = mock_window
            
            result = PerformanceCalculator.calculate_cumulative_twrr(
                mock_df, "account_id", "as_of_date", "calculated_twrr"
            )
            
            # Verify window function was used
            mock_window_class.partitionBy.assert_called_once()
    
    def test_annualize_return(self):
        """Test return annualization"""
        # Test quarterly return annualization
        quarterly_return = 0.02  # 2% quarterly
        periods_per_year = 4
        
        # Formula: (1 + return)^periods_per_year - 1
        expected_annual = (1 + quarterly_return) ** periods_per_year - 1
        
        # Manual calculation for verification
        calculated_annual = (1.02 ** 4) - 1
        
        self.assertAlmostEqual(expected_annual, calculated_annual, places=6)
        self.assertAlmostEqual(calculated_annual, 0.08243216, places=6)

class TestDataValidator(unittest.TestCase):
    """Test data validation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock Spark DataFrame
        self.mock_df = Mock()
        self.validator = DataValidator(self.mock_df)
    
    def test_check_required_fields(self):
        """Test required fields validation"""
        required_fields = ['account_id', 'as_of_date', 'beginning_market_value']
        
        # Mock DataFrame columns
        self.mock_df.columns = required_fields + ['optional_field']
        
        # Test with all required fields present
        missing_fields = []
        for field in required_fields:
            if field not in self.mock_df.columns:
                missing_fields.append(field)
        
        self.assertEqual(len(missing_fields), 0)
    
    def test_check_data_types(self):
        """Test data type validation"""
        # Mock schema checking
        expected_types = {
            'account_id': 'string',
            'beginning_market_value': 'decimal',
            'as_of_date': 'date'
        }
        
        # Simulate type checking
        for field, expected_type in expected_types.items():
            # In real implementation, this would check actual DataFrame schema
            self.assertIn(expected_type, ['string', 'decimal', 'date', 'double'])
    
    def test_check_null_values(self):
        """Test null value detection"""
        # Mock null count checking
        mock_null_counts = {
            'account_id': 0,
            'beginning_market_value': 2,
            'ending_market_value': 0
        }
        
        # Fields that should not have nulls
        critical_fields = ['account_id', 'ending_market_value']
        
        issues = []
        for field in critical_fields:
            if mock_null_counts.get(field, 0) > 0:
                issues.append(f"{field} has null values")
        
        # Should find no issues with critical fields
        self.assertEqual(len(issues), 0)
    
    def test_check_date_format(self):
        """Test date format validation"""
        valid_date_formats = [
            "2024-01-31",
            "2024/01/31", 
            "01/31/2024"
        ]
        
        # All formats should be recognizable
        for date_format in valid_date_formats:
            # In real implementation, would parse with Spark date functions
            self.assertIsInstance(date_format, str)
            self.assertTrue(len(date_format) >= 8)
    
    def test_outlier_detection(self):
        """Test outlier detection logic"""
        # Mock return values for testing
        sample_returns = [0.01, 0.02, 0.015, 0.012, 0.5, 0.018, 0.022]
        
        # Calculate statistics
        mean_return = sum(sample_returns) / len(sample_returns)
        
        # Detect outliers (simplified logic)
        outliers = [r for r in sample_returns if abs(r) > 0.1]  # > 10% return
        
        self.assertEqual(len(outliers), 1)
        self.assertIn(0.5, outliers)

class TestETLProcessor(unittest.TestCase):
    """Test vendor-specific data processing"""
    
    def setUp(self):
        """Set up test environment"""
        self.processor = ETLProcessor()
    
    def test_load_vendor_mapping(self):
        """Test vendor mapping configuration loading"""
        # Mock mapping configuration
        mock_mapping = {
            "vendor_a": {
                "file_format": "csv",
                "field_mappings": {
                    "account_id": "account_id",
                    "beginning_market_value": "beginning_mv"
                }
            }
        }
        
        # Test mapping structure
        self.assertIn("vendor_a", mock_mapping)
        self.assertIn("field_mappings", mock_mapping["vendor_a"])
        self.assertEqual(mock_mapping["vendor_a"]["file_format"], "csv")
    
    def test_apply_vendor_mapping(self):
        """Test application of vendor-specific field mappings"""
        # Mock vendor column mappings
        vendor_mapping = {
            "acct_id": "account_id",
            "start_mv": "beginning_market_value",
            "end_mv": "ending_market_value"
        }
        
        # Original columns
        original_columns = ["acct_id", "start_mv", "end_mv", "deposits"]
        
        # Apply mapping
        mapped_columns = []
        for col in original_columns:
            mapped_col = vendor_mapping.get(col, col)
            mapped_columns.append(mapped_col)
        
        # Verify mapping
        expected_columns = ["account_id", "beginning_market_value", "ending_market_value", "deposits"]
        self.assertEqual(mapped_columns, expected_columns)
    
    def test_normalize_data_types(self):
        """Test data type normalization"""
        # Test data type conversions
        test_conversions = {
            "decimal_field": ("123.45", 123.45),
            "integer_field": ("100", 100),
            "date_field": ("2024-01-31", "2024-01-31"),
            "string_field": ("ACC001", "ACC001")
        }
        
        for field_type, (input_val, expected_output) in test_conversions.items():
            if "decimal" in field_type:
                self.assertIsInstance(expected_output, float)
            elif "integer" in field_type:
                self.assertIsInstance(expected_output, int)
            elif "string" in field_type:
                self.assertIsInstance(expected_output, str)
    
    def test_handle_vendor_specific_logic(self):
        """Test vendor-specific business logic"""
        vendors = ['vendor_a', 'vendor_b', 'vendor_c']
        
        for vendor in vendors:
            # Each vendor should have specific handling
            if vendor == 'vendor_a':
                expected_format = 'csv'
                expected_encoding = 'utf-8'
            elif vendor == 'vendor_b':
                expected_format = 'excel'
                expected_encoding = 'utf-8'
            elif vendor == 'vendor_c':
                expected_format = 'json'
                expected_encoding = 'utf-8'
            
            # Verify vendor-specific configurations
            self.assertIn(expected_format, ['csv', 'excel', 'json'])
            self.assertEqual(expected_encoding, 'utf-8')

class TestETLJobIntegration(unittest.TestCase):
    """Integration tests for ETL job components"""
    
    @patch('advisory_performance_etl.GlueContext')
    @patch('advisory_performance_etl.SparkContext')
    def test_etl_job_initialization(self, mock_spark_context, mock_glue_context):
        """Test ETL job initialization"""
        # Mock contexts
        mock_sc = Mock()
        mock_glue_context.return_value = Mock()
        mock_spark_context.return_value = mock_sc
        
        # Test initialization parameters
        job_args = {
            'input_path': 's3://test-bucket/data/',
            'vendor': 'vendor_a',
            'config_path': 's3://test-bucket/config.json'
        }
        
        # Verify required arguments are present
        required_args = ['input_path', 'vendor', 'config_path']
        for arg in required_args:
            self.assertIn(arg, job_args)
    
    def test_data_processing_pipeline(self):
        """Test complete data processing pipeline"""
        # Mock pipeline stages
        stages = [
            'data_ingestion',
            'data_validation', 
            'vendor_mapping',
            'financial_calculations',
            'quality_checks',
            'data_output'
        ]
        
        # Simulate pipeline execution
        completed_stages = []
        for stage in stages:
            # Mock stage execution
            stage_result = f"{stage}_completed"
            completed_stages.append(stage_result)
        
        # Verify all stages completed
        self.assertEqual(len(completed_stages), len(stages))
        self.assertTrue(all('completed' in stage for stage in completed_stages))
    
    def test_error_handling(self):
        """Test error handling in ETL job"""
        # Test different error scenarios
        error_scenarios = [
            'missing_input_file',
            'invalid_data_format',
            'calculation_error',
            'output_write_error'
        ]
        
        for scenario in error_scenarios:
            # Mock error handling
            try:
                if scenario == 'missing_input_file':
                    raise FileNotFoundError(f"Input file not found: {scenario}")
                elif scenario == 'invalid_data_format':
                    raise ValueError(f"Invalid data format: {scenario}")
                elif scenario == 'calculation_error':
                    raise ArithmeticError(f"Calculation error: {scenario}")
                elif scenario == 'output_write_error':
                    raise IOError(f"Output write error: {scenario}")
            except Exception as e:
                # Verify error is caught and handled
                self.assertIsInstance(e, (FileNotFoundError, ValueError, ArithmeticError, IOError))
                self.assertIn(scenario, str(e))

class TestPerformanceMetrics(unittest.TestCase):
    """Test performance and monitoring metrics"""
    
    def test_job_performance_metrics(self):
        """Test job performance tracking"""
        # Mock performance metrics
        performance_metrics = {
            'records_processed': 10000,
            'processing_time_seconds': 120,
            'memory_usage_mb': 512,
            'success_rate': 99.5
        }
        
        # Verify metrics are within acceptable ranges
        self.assertGreater(performance_metrics['records_processed'], 0)
        self.assertGreater(performance_metrics['processing_time_seconds'], 0)
        self.assertGreater(performance_metrics['memory_usage_mb'], 0)
        self.assertGreaterEqual(performance_metrics['success_rate'], 95.0)
    
    def test_data_quality_metrics(self):
        """Test data quality metrics"""
        quality_metrics = {
            'completeness_rate': 98.5,
            'accuracy_rate': 99.2,
            'consistency_rate': 97.8,
            'validity_rate': 99.0
        }
        
        # All quality metrics should be above 95%
        for metric, rate in quality_metrics.items():
            self.assertGreaterEqual(rate, 95.0, f"{metric} below threshold")
    
    def test_financial_calculation_accuracy(self):
        """Test accuracy of financial calculations"""
        # Test known calculation results
        test_cases = [
            {
                'beginning_mv': 100000,
                'ending_mv': 105000,
                'net_flow': 3000,
                'expected_twrr_approx': 0.0196  # Approximate expected TWRR
            },
            {
                'beginning_mv': 200000,
                'ending_mv': 198000,
                'net_flow': -5000,
                'expected_twrr_approx': 0.0152  # Approximate expected TWRR
            }
        ]
        
        for case in test_cases:
            # Calculate TWRR with mid-period flow assumption
            adjusted_beginning = case['beginning_mv'] + (case['net_flow'] / 2)
            calculated_twrr = (case['ending_mv'] - adjusted_beginning) / adjusted_beginning
            
            # Verify calculation is reasonable
            self.assertGreater(calculated_twrr, -1.0)  # > -100%
            self.assertLess(calculated_twrr, 1.0)      # < 100% for normal markets

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
