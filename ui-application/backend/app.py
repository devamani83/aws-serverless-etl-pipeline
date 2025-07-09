"""
Flask backend API for Advisory Performance ETL UI
Provides endpoints for viewing vendor data, validation results, and reconciliation reports
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import psycopg2
import pandas as pd
import json
import os
import boto3
from datetime import datetime, timedelta
import logging
from decimal import Decimal
import io
import base64

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

class DatabaseManager:
    """Handles database connections and queries"""
    
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager')
        self.db_config = self.get_database_config()
    
    def get_database_config(self):
        """Get database configuration from environment and secrets"""
        try:
            # Get password from Secrets Manager
            secret_name = os.environ.get('DB_PASSWORD_SECRET', 'advisory-etl/db-password')
            secret_response = self.secrets_client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(secret_response['SecretString'])
            
            return {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'port': int(os.environ.get('DB_PORT', 5432)),
                'database': os.environ.get('DB_NAME', 'advisory_performance'),
                'username': os.environ.get('DB_USERNAME', 'postgres'),
                'password': secret_data.get('password', 'password')
            }
        except Exception as e:
            logger.error(f"Failed to get database config: {str(e)}")
            # Fallback to environment variables for local development
            return {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'port': int(os.environ.get('DB_PORT', 5432)),
                'database': os.environ.get('DB_NAME', 'advisory_performance'),
                'username': os.environ.get('DB_USERNAME', 'postgres'),
                'password': os.environ.get('DB_PASSWORD', 'password')
            }
    
    def get_connection(self):
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

# Initialize database manager
db_manager = DatabaseManager()

def decimal_default(obj):
    """JSON serializer for decimal objects"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/api/vendors', methods=['GET'])
def get_vendors():
    """Get list of all vendors"""
    try:
        conn = db_manager.get_connection()
        query = """
        SELECT DISTINCT data_source as vendor_name, 
               COUNT(*) as file_count,
               MAX(created_at) as last_processed
        FROM performance_data 
        GROUP BY data_source
        ORDER BY data_source
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        vendors = df.to_dict('records')
        return jsonify(vendors)
        
    except Exception as e:
        logger.error(f"Failed to get vendors: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def get_files():
    """Get list of processed files with optional vendor filter"""
    try:
        vendor = request.args.get('vendor')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        conn = db_manager.get_connection()
        
        base_query = """
        SELECT DISTINCT 
            file_name,
            data_source as vendor,
            COUNT(*) as record_count,
            MIN(created_at) as processing_start,
            MAX(updated_at) as last_updated,
            CASE 
                WHEN COUNT(CASE WHEN reconciliation_status = 'COMPLETED' THEN 1 END) = COUNT(*) 
                THEN 'COMPLETED'
                WHEN COUNT(CASE WHEN reconciliation_status = 'COMPLETED_WITH_ISSUES' THEN 1 END) > 0 
                THEN 'COMPLETED_WITH_ISSUES'
                ELSE 'PROCESSING'
            END as overall_status
        FROM performance_data 
        """
        
        params = []
        if vendor:
            base_query += " WHERE data_source = %s"
            params.append(vendor)
        
        base_query += """
        GROUP BY file_name, data_source
        ORDER BY MAX(updated_at) DESC
        LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        df = pd.read_sql_query(base_query, conn, params=params)
        conn.close()
        
        files = df.to_dict('records')
        return jsonify(files)
        
    except Exception as e:
        logger.error(f"Failed to get files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/file/<file_name>/details', methods=['GET'])
def get_file_details(file_name):
    """Get detailed information about a specific file"""
    try:
        vendor = request.args.get('vendor')
        
        conn = db_manager.get_connection()
        
        # Get file summary
        summary_query = """
        SELECT 
            file_name,
            data_source as vendor,
            COUNT(*) as total_records,
            COUNT(DISTINCT account_id) as unique_accounts,
            MIN(as_of_date) as earliest_date,
            MAX(as_of_date) as latest_date,
            SUM(ending_market_value) as total_market_value,
            AVG(calculated_twrr) as avg_twrr,
            COUNT(CASE WHEN twrr_tolerance_check = false THEN 1 END) as twrr_failures
        FROM performance_data 
        WHERE file_name = %s
        """
        
        params = [file_name]
        if vendor:
            summary_query += " AND data_source = %s"
            params.append(vendor)
        
        summary_query += " GROUP BY file_name, data_source"
        
        summary_df = pd.read_sql_query(summary_query, conn, params=params)
        
        # Get sample records
        sample_query = """
        SELECT * FROM performance_data 
        WHERE file_name = %s
        """
        
        sample_params = [file_name]
        if vendor:
            sample_query += " AND data_source = %s"
            sample_params.append(vendor)
        
        sample_query += " ORDER BY account_id, as_of_date LIMIT 10"
        
        sample_df = pd.read_sql_query(sample_query, conn, sample_params)
        conn.close()
        
        response = {
            'summary': summary_df.to_dict('records')[0] if len(summary_df) > 0 else {},
            'sample_records': sample_df.to_dict('records')
        }
        
        return jsonify(response, default=decimal_default)
        
    except Exception as e:
        logger.error(f"Failed to get file details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reconciliation/results', methods=['GET'])
def get_reconciliation_results():
    """Get reconciliation results with filtering options"""
    try:
        file_name = request.args.get('file_name')
        vendor = request.args.get('vendor')
        account_id = request.args.get('account_id')
        field_name = request.args.get('field_name')
        tolerance_failures_only = request.args.get('tolerance_failures_only', 'false').lower() == 'true'
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        conn = db_manager.get_connection()
        
        query = """
        SELECT 
            r.*,
            p.data_source as vendor,
            p.file_name
        FROM reconciliation_results r
        JOIN performance_data p ON r.account_id = p.account_id AND r.as_of_date = p.as_of_date
        WHERE 1=1
        """
        
        params = []
        
        if file_name:
            query += " AND p.file_name = %s"
            params.append(file_name)
        
        if vendor:
            query += " AND p.data_source = %s"
            params.append(vendor)
        
        if account_id:
            query += " AND r.account_id = %s"
            params.append(account_id)
        
        if field_name:
            query += " AND r.field_name = %s"
            params.append(field_name)
        
        if tolerance_failures_only:
            query += " AND r.within_tolerance = false"
        
        query += " ORDER BY r.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        results = df.to_dict('records')
        return jsonify(results, default=decimal_default)
        
    except Exception as e:
        logger.error(f"Failed to get reconciliation results: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/reconciliation/summary', methods=['GET'])
def get_reconciliation_summary():
    """Get reconciliation summary statistics"""
    try:
        file_name = request.args.get('file_name')
        vendor = request.args.get('vendor')
        days_back = int(request.args.get('days_back', 30))
        
        conn = db_manager.get_connection()
        
        date_filter = datetime.now() - timedelta(days=days_back)
        
        query = """
        SELECT 
            r.field_name,
            COUNT(*) as total_checks,
            COUNT(CASE WHEN r.within_tolerance = true THEN 1 END) as passed_checks,
            COUNT(CASE WHEN r.within_tolerance = false THEN 1 END) as failed_checks,
            AVG(r.variance) as avg_variance,
            MAX(r.variance) as max_variance,
            ROUND(COUNT(CASE WHEN r.within_tolerance = true THEN 1 END) * 100.0 / COUNT(*), 2) as pass_rate
        FROM reconciliation_results r
        JOIN performance_data p ON r.account_id = p.account_id AND r.as_of_date = p.as_of_date
        WHERE r.created_at >= %s
        """
        
        params = [date_filter]
        
        if file_name:
            query += " AND p.file_name = %s"
            params.append(file_name)
        
        if vendor:
            query += " AND p.data_source = %s"
            params.append(vendor)
        
        query += " GROUP BY r.field_name ORDER BY pass_rate ASC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        summary = df.to_dict('records')
        return jsonify(summary, default=decimal_default)
        
    except Exception as e:
        logger.error(f"Failed to get reconciliation summary: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Get account information with performance summary"""
    try:
        file_name = request.args.get('file_name')
        vendor = request.args.get('vendor')
        search = request.args.get('search', '')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        conn = db_manager.get_connection()
        
        query = """
        SELECT 
            account_id,
            data_source as vendor,
            file_name,
            as_of_date,
            beginning_market_value,
            ending_market_value,
            calculated_twrr,
            vendor_twrr,
            twrr_variance,
            twrr_tolerance_check,
            net_flow,
            cumulative_net_flow,
            reconciliation_status
        FROM performance_data 
        WHERE 1=1
        """
        
        params = []
        
        if file_name:
            query += " AND file_name = %s"
            params.append(file_name)
        
        if vendor:
            query += " AND data_source = %s"
            params.append(vendor)
        
        if search:
            query += " AND account_id ILIKE %s"
            params.append(f"%{search}%")
        
        query += " ORDER BY account_id, as_of_date DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        accounts = df.to_dict('records')
        return jsonify(accounts, default=decimal_default)
        
    except Exception as e:
        logger.error(f"Failed to get accounts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/account/<account_id>/history', methods=['GET'])
def get_account_history(account_id):
    """Get historical performance data for a specific account"""
    try:
        vendor = request.args.get('vendor')
        months_back = int(request.args.get('months_back', 12))
        
        conn = db_manager.get_connection()
        
        date_filter = datetime.now() - timedelta(days=months_back * 30)
        
        query = """
        SELECT 
            as_of_date,
            beginning_market_value,
            ending_market_value,
            net_flow,
            calculated_twrr,
            vendor_twrr,
            cumulative_twrr,
            twrr_variance,
            twrr_tolerance_check
        FROM performance_data 
        WHERE account_id = %s AND as_of_date >= %s
        """
        
        params = [account_id, date_filter]
        
        if vendor:
            query += " AND data_source = %s"
            params.append(vendor)
        
        query += " ORDER BY as_of_date ASC"
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        
        history = df.to_dict('records')
        return jsonify(history, default=decimal_default)
        
    except Exception as e:
        logger.error(f"Failed to get account history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    """Get key metrics for dashboard"""
    try:
        days_back = int(request.args.get('days_back', 7))
        date_filter = datetime.now() - timedelta(days=days_back)
        
        conn = db_manager.get_connection()
        
        # Overall metrics
        metrics_query = """
        SELECT 
            COUNT(DISTINCT file_name) as total_files_processed,
            COUNT(DISTINCT data_source) as total_vendors,
            COUNT(DISTINCT account_id) as total_accounts,
            COUNT(*) as total_records,
            SUM(ending_market_value) as total_aum,
            AVG(calculated_twrr) as avg_twrr
        FROM performance_data 
        WHERE created_at >= %s
        """
        
        metrics_df = pd.read_sql_query(metrics_query, conn, params=[date_filter])
        
        # Reconciliation metrics
        recon_query = """
        SELECT 
            COUNT(*) as total_recon_checks,
            COUNT(CASE WHEN within_tolerance = true THEN 1 END) as passed_checks,
            ROUND(COUNT(CASE WHEN within_tolerance = true THEN 1 END) * 100.0 / COUNT(*), 2) as overall_pass_rate
        FROM reconciliation_results 
        WHERE created_at >= %s
        """
        
        recon_df = pd.read_sql_query(recon_query, conn, params=[date_filter])
        
        # Daily processing volume
        daily_query = """
        SELECT 
            DATE(created_at) as processing_date,
            COUNT(DISTINCT file_name) as files_processed,
            COUNT(*) as records_processed
        FROM performance_data 
        WHERE created_at >= %s
        GROUP BY DATE(created_at)
        ORDER BY processing_date DESC
        """
        
        daily_df = pd.read_sql_query(daily_query, conn, params=[date_filter])
        
        conn.close()
        
        response = {
            'overall_metrics': metrics_df.to_dict('records')[0] if len(metrics_df) > 0 else {},
            'reconciliation_metrics': recon_df.to_dict('records')[0] if len(recon_df) > 0 else {},
            'daily_processing': daily_df.to_dict('records')
        }
        
        return jsonify(response, default=decimal_default)
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/reconciliation-report', methods=['GET'])
def export_reconciliation_report():
    """Export reconciliation report as CSV"""
    try:
        file_name = request.args.get('file_name')
        vendor = request.args.get('vendor')
        
        if not file_name or not vendor:
            return jsonify({'error': 'file_name and vendor are required'}), 400
        
        conn = db_manager.get_connection()
        
        query = """
        SELECT 
            r.account_id,
            r.as_of_date,
            r.field_name,
            r.calculated_value,
            r.vendor_value,
            r.variance,
            r.tolerance_threshold,
            r.within_tolerance,
            r.notes,
            p.beginning_market_value,
            p.ending_market_value,
            p.calculated_twrr,
            p.vendor_twrr
        FROM reconciliation_results r
        JOIN performance_data p ON r.account_id = p.account_id AND r.as_of_date = p.as_of_date
        WHERE p.file_name = %s AND p.data_source = %s
        ORDER BY r.account_id, r.as_of_date, r.field_name
        """
        
        df = pd.read_sql_query(query, conn, params=[file_name, vendor])
        conn.close()
        
        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Convert to bytes
        csv_data = output.getvalue().encode('utf-8')
        
        return jsonify({
            'data': base64.b64encode(csv_data).decode('utf-8'),
            'filename': f'reconciliation_report_{file_name}_{vendor}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
        
    except Exception as e:
        logger.error(f"Failed to export reconciliation report: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
