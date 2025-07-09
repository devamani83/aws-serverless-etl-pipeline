"""
Lambda function for account reconciliation and tolerance checking
Compares calculated values with vendor-provided values
"""

import json
import boto3
import logging
import os
import psycopg2
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import pandas as pd

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ReconciliationEngine:
    """Handles account reconciliation and tolerance checking"""
    
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager')
        self.s3_client = boto3.client('s3')
        
        # Get database connection details
        self.db_config = self.get_database_config()
        
        # Tolerance thresholds
        self.tolerance_thresholds = {
            'twrr_tolerance': Decimal('0.0001'),  # 1 basis point
            'market_value_tolerance': Decimal('0.01'),  # 1 cent
            'netflow_tolerance': Decimal('0.01'),  # 1 cent
            'percentage_tolerance': Decimal('0.001')  # 0.1%
        }
    
    def get_database_config(self):
        """Get database configuration from environment and secrets"""
        try:
            # Get password from Secrets Manager
            secret_name = os.environ.get('DB_PASSWORD_SECRET', 'advisory-etl/db-password')
            secret_response = self.secrets_client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(secret_response['SecretString'])
            
            return {
                'host': os.environ.get('DB_HOST'),
                'port': int(os.environ.get('DB_PORT', 5432)),
                'database': os.environ.get('DB_NAME', 'advisory_performance'),
                'username': os.environ.get('DB_USERNAME'),
                'password': secret_data['password']
            }
        except Exception as e:
            logger.error(f"Failed to get database config: {str(e)}")
            raise
    
    def get_database_connection(self):
        """Create database connection"""
        try:
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                database=self.db_config['database'],
                user=self.db_config['username'],
                password=self.db_config['password']
            )
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def get_processed_data(self, file_name, vendor):
        """Retrieve processed data from database for reconciliation"""
        query = """
        SELECT 
            account_id,
            as_of_date,
            beginning_market_value,
            ending_market_value,
            contributions,
            distributions,
            income,
            appreciation,
            fees,
            other_adjustments,
            net_flow,
            cumulative_net_flow,
            calculated_twrr,
            cumulative_twrr,
            vendor_twrr,
            benchmark_return,
            twrr_variance,
            twrr_tolerance_check
        FROM performance_data 
        WHERE file_name = %s AND data_source = %s
        ORDER BY account_id, as_of_date
        """
        
        try:
            conn = self.get_database_connection()
            df = pd.read_sql_query(query, conn, params=(file_name, vendor))
            conn.close()
            
            logger.info(f"Retrieved {len(df)} records for reconciliation")
            return df
            
        except Exception as e:
            logger.error(f"Failed to retrieve processed data: {str(e)}")
            raise
    
    def calculate_market_value_reconciliation(self, row):
        """
        Reconcile market value calculation:
        Ending MV = Beginning MV + Net Flow + Income + Appreciation - Fees + Other Adjustments
        """
        beginning_mv = Decimal(str(row['beginning_market_value'] or 0))
        ending_mv = Decimal(str(row['ending_market_value'] or 0))
        net_flow = Decimal(str(row['net_flow'] or 0))
        income = Decimal(str(row['income'] or 0))
        appreciation = Decimal(str(row['appreciation'] or 0))
        fees = Decimal(str(row['fees'] or 0))
        other_adjustments = Decimal(str(row['other_adjustments'] or 0))
        
        calculated_ending_mv = beginning_mv + net_flow + income + appreciation - fees + other_adjustments
        variance = abs(ending_mv - calculated_ending_mv)
        
        within_tolerance = variance <= self.tolerance_thresholds['market_value_tolerance']
        
        return {
            'field_name': 'ending_market_value',
            'calculated_value': float(calculated_ending_mv),
            'vendor_value': float(ending_mv),
            'variance': float(variance),
            'tolerance_threshold': float(self.tolerance_thresholds['market_value_tolerance']),
            'within_tolerance': within_tolerance
        }
    
    def calculate_twrr_reconciliation(self, row):
        """Reconcile TWRR calculation with vendor-provided value"""
        calculated_twrr = row['calculated_twrr']
        vendor_twrr = row['vendor_twrr']
        
        if calculated_twrr is None or vendor_twrr is None:
            return {
                'field_name': 'twrr',
                'calculated_value': calculated_twrr,
                'vendor_value': vendor_twrr,
                'variance': None,
                'tolerance_threshold': float(self.tolerance_thresholds['twrr_tolerance']),
                'within_tolerance': None,
                'notes': 'Missing TWRR values'
            }
        
        calculated_twrr = Decimal(str(calculated_twrr))
        vendor_twrr = Decimal(str(vendor_twrr))
        variance = abs(calculated_twrr - vendor_twrr)
        
        within_tolerance = variance <= self.tolerance_thresholds['twrr_tolerance']
        
        return {
            'field_name': 'twrr',
            'calculated_value': float(calculated_twrr),
            'vendor_value': float(vendor_twrr),
            'variance': float(variance),
            'tolerance_threshold': float(self.tolerance_thresholds['twrr_tolerance']),
            'within_tolerance': within_tolerance
        }
    
    def calculate_net_flow_reconciliation(self, row):
        """Reconcile net flow calculation"""
        contributions = Decimal(str(row['contributions'] or 0))
        distributions = Decimal(str(row['distributions'] or 0))
        calculated_net_flow = contributions - distributions
        
        stored_net_flow = Decimal(str(row['net_flow'] or 0))
        variance = abs(calculated_net_flow - stored_net_flow)
        
        within_tolerance = variance <= self.tolerance_thresholds['netflow_tolerance']
        
        return {
            'field_name': 'net_flow',
            'calculated_value': float(calculated_net_flow),
            'vendor_value': float(stored_net_flow),
            'variance': float(variance),
            'tolerance_threshold': float(self.tolerance_thresholds['netflow_tolerance']),
            'within_tolerance': within_tolerance
        }
    
    def perform_cross_account_validation(self, df):
        """Perform cross-account validation for portfolio-level consistency"""
        validations = []
        
        # Group by portfolio if available
        if 'portfolio_id' in df.columns:
            portfolio_groups = df.groupby('portfolio_id')
            
            for portfolio_id, portfolio_data in portfolio_groups:
                # Check for consistent dates across accounts in same portfolio
                unique_dates = portfolio_data['as_of_date'].nunique()
                total_accounts = portfolio_data['account_id'].nunique()
                
                if unique_dates > 1:
                    validations.append({
                        'validation_type': 'portfolio_date_consistency',
                        'portfolio_id': portfolio_id,
                        'issue': f'Inconsistent dates across accounts in portfolio',
                        'details': {
                            'unique_dates': int(unique_dates),
                            'total_accounts': int(total_accounts)
                        },
                        'severity': 'WARNING'
                    })
                
                # Check for extreme TWRR outliers
                if 'calculated_twrr' in portfolio_data.columns:
                    twrr_values = portfolio_data['calculated_twrr'].dropna()
                    if len(twrr_values) > 1:
                        mean_twrr = twrr_values.mean()
                        std_twrr = twrr_values.std()
                        
                        # Flag accounts with TWRR > 3 standard deviations from mean
                        outliers = portfolio_data[
                            abs(portfolio_data['calculated_twrr'] - mean_twrr) > 3 * std_twrr
                        ]
                        
                        if len(outliers) > 0:
                            validations.append({
                                'validation_type': 'twrr_outlier_detection',
                                'portfolio_id': portfolio_id,
                                'issue': 'Potential TWRR outliers detected',
                                'details': {
                                    'outlier_accounts': outliers['account_id'].tolist(),
                                    'mean_twrr': float(mean_twrr),
                                    'std_twrr': float(std_twrr)
                                },
                                'severity': 'WARNING'
                            })
        
        return validations
    
    def save_reconciliation_results(self, reconciliation_results):
        """Save reconciliation results to database"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO reconciliation_results (
                account_id, as_of_date, field_name, calculated_value, 
                vendor_value, variance, tolerance_threshold, within_tolerance, notes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            for result in reconciliation_results:
                cursor.execute(insert_query, (
                    result['account_id'],
                    result['as_of_date'],
                    result['field_name'],
                    result['calculated_value'],
                    result['vendor_value'],
                    result['variance'],
                    result['tolerance_threshold'],
                    result['within_tolerance'],
                    result.get('notes', '')
                ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Saved {len(reconciliation_results)} reconciliation results")
            
        except Exception as e:
            logger.error(f"Failed to save reconciliation results: {str(e)}")
            raise
    
    def update_reconciliation_status(self, file_name, vendor, overall_status):
        """Update reconciliation status in performance_data table"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            update_query = """
            UPDATE performance_data 
            SET reconciliation_status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE file_name = %s AND data_source = %s
            """
            
            cursor.execute(update_query, (overall_status, file_name, vendor))
            conn.commit()
            cursor.close()
            conn.close()
            
            logger.info(f"Updated reconciliation status to {overall_status}")
            
        except Exception as e:
            logger.error(f"Failed to update reconciliation status: {str(e)}")
            raise
    
    def generate_reconciliation_report(self, reconciliation_results, cross_validations):
        """Generate comprehensive reconciliation report"""
        total_checks = len(reconciliation_results)
        passed_checks = sum(1 for r in reconciliation_results if r['within_tolerance'])
        failed_checks = total_checks - passed_checks
        
        # Calculate pass rate
        pass_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
        
        # Categorize failures by field
        failures_by_field = {}
        for result in reconciliation_results:
            if not result['within_tolerance']:
                field = result['field_name']
                if field not in failures_by_field:
                    failures_by_field[field] = []
                failures_by_field[field].append(result)
        
        # Count validation issues by severity
        validation_summary = {}
        for validation in cross_validations:
            severity = validation['severity']
            validation_summary[severity] = validation_summary.get(severity, 0) + 1
        
        report = {
            'reconciliation_summary': {
                'total_checks': total_checks,
                'passed_checks': passed_checks,
                'failed_checks': failed_checks,
                'pass_rate_percentage': round(pass_rate, 2)
            },
            'failures_by_field': failures_by_field,
            'cross_validation_summary': validation_summary,
            'detailed_results': reconciliation_results,
            'cross_validations': cross_validations,
            'overall_status': 'PASS' if failed_checks == 0 and len([v for v in cross_validations if v['severity'] == 'ERROR']) == 0 else 'FAIL',
            'recommendation': self.get_recommendation(pass_rate, failed_checks, cross_validations)
        }
        
        return report
    
    def get_recommendation(self, pass_rate, failed_checks, cross_validations):
        """Generate recommendations based on reconciliation results"""
        recommendations = []
        
        if pass_rate < 95:
            recommendations.append("Low pass rate detected. Review calculation logic and data quality.")
        
        if failed_checks > 0:
            recommendations.append(f"{failed_checks} reconciliation checks failed. Investigate tolerance thresholds and data accuracy.")
        
        error_validations = [v for v in cross_validations if v['severity'] == 'ERROR']
        if error_validations:
            recommendations.append("Critical validation errors detected. Manual review required.")
        
        warning_validations = [v for v in cross_validations if v['severity'] == 'WARNING']
        if warning_validations:
            recommendations.append("Data quality warnings detected. Consider additional validation rules.")
        
        if not recommendations:
            recommendations.append("All reconciliation checks passed. Data quality is acceptable.")
        
        return recommendations
    
    def reconcile_file_data(self, file_name, vendor):
        """Main reconciliation function for a processed file"""
        try:
            logger.info(f"Starting reconciliation for file: {file_name}, vendor: {vendor}")
            
            # Get processed data
            df = self.get_processed_data(file_name, vendor)
            
            if df.empty:
                logger.warning(f"No data found for file {file_name}")
                return {
                    'status': 'NO_DATA',
                    'message': 'No processed data found for reconciliation'
                }
            
            reconciliation_results = []
            
            # Perform reconciliation for each record
            for _, row in df.iterrows():
                account_id = row['account_id']
                as_of_date = row['as_of_date']
                
                # Market value reconciliation
                mv_result = self.calculate_market_value_reconciliation(row)
                mv_result['account_id'] = account_id
                mv_result['as_of_date'] = as_of_date
                reconciliation_results.append(mv_result)
                
                # TWRR reconciliation
                twrr_result = self.calculate_twrr_reconciliation(row)
                twrr_result['account_id'] = account_id
                twrr_result['as_of_date'] = as_of_date
                reconciliation_results.append(twrr_result)
                
                # Net flow reconciliation
                nf_result = self.calculate_net_flow_reconciliation(row)
                nf_result['account_id'] = account_id
                nf_result['as_of_date'] = as_of_date
                reconciliation_results.append(nf_result)
            
            # Perform cross-account validations
            cross_validations = self.perform_cross_account_validation(df)
            
            # Save results to database
            self.save_reconciliation_results(reconciliation_results)
            
            # Generate comprehensive report
            report = self.generate_reconciliation_report(reconciliation_results, cross_validations)
            
            # Update reconciliation status
            overall_status = 'COMPLETED' if report['overall_status'] == 'PASS' else 'COMPLETED_WITH_ISSUES'
            self.update_reconciliation_status(file_name, vendor, overall_status)
            
            logger.info(f"Reconciliation completed: {report['reconciliation_summary']}")
            
            return {
                'status': 'SUCCESS',
                'report': report,
                'file_name': file_name,
                'vendor': vendor
            }
            
        except Exception as e:
            logger.error(f"Reconciliation failed: {str(e)}")
            return {
                'status': 'FAILED',
                'error': str(e),
                'file_name': file_name,
                'vendor': vendor
            }

def lambda_handler(event, context):
    """Lambda handler for reconciliation"""
    logger.info(f"Received reconciliation request: {json.dumps(event)}")
    
    try:
        # Extract parameters
        file_name = event.get('file_name')
        vendor = event.get('vendor')
        
        if not file_name or not vendor:
            raise ValueError("file_name and vendor are required parameters")
        
        # Initialize reconciliation engine
        reconciler = ReconciliationEngine()
        
        # Perform reconciliation
        result = reconciler.reconcile_file_data(file_name, vendor)
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'FAILED',
                'error': str(e)
            })
        }
