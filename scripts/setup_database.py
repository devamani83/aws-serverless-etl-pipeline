"""
Database setup script for Advisory Performance ETL Pipeline
Creates the database schema and initial data
"""

import os
import json
import boto3
import psycopg2
import logging
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Handles database setup and initialization"""
    
    def __init__(self):
        self.secrets_client = boto3.client('secretsmanager')
        self.cloudformation_client = boto3.client('cloudformation')
        
    def get_database_config(self):
        """Get database configuration from CloudFormation and Secrets Manager"""
        try:
            # Get database endpoint from CloudFormation
            response = self.cloudformation_client.describe_stacks(
                StackName='AdvisoryPerformanceETLStack'
            )
            
            outputs = response['Stacks'][0]['Outputs']
            db_endpoint = None
            
            for output in outputs:
                if output['OutputKey'] == 'DatabaseEndpoint':
                    db_endpoint = output['OutputValue']
                    break
            
            if not db_endpoint:
                raise ValueError("Database endpoint not found in CloudFormation outputs")
            
            # Get database password from Secrets Manager
            secret_response = self.secrets_client.get_secret_value(
                SecretId='advisory-etl/db-password'
            )
            secret_data = json.loads(secret_response['SecretString'])
            
            return {
                'host': db_endpoint,
                'port': 5432,
                'database': 'advisory_performance',
                'username': secret_data['username'],
                'password': secret_data['password']
            }
            
        except Exception as e:
            logger.error(f"Failed to get database config: {str(e)}")
            raise
    
    def create_connection(self, config, database=None):
        """Create database connection"""
        try:
            conn_config = config.copy()
            if database:
                conn_config['database'] = database
            
            conn = psycopg2.connect(**conn_config)
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def create_database_if_not_exists(self, config):
        """Create database if it doesn't exist"""
        try:
            # Connect to postgres database to create our database
            postgres_config = config.copy()
            postgres_config['database'] = 'postgres'
            
            conn = self.create_connection(postgres_config)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (config['database'],)
            )
            
            if not cursor.fetchone():
                logger.info(f"Creating database {config['database']}")
                cursor.execute(f"CREATE DATABASE {config['database']}")
            else:
                logger.info(f"Database {config['database']} already exists")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create database: {str(e)}")
            raise
    
    def execute_schema_file(self, config, schema_file):
        """Execute SQL schema file"""
        try:
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            conn = self.create_connection(config)
            cursor = conn.cursor()
            
            # Execute schema
            cursor.execute(schema_sql)
            conn.commit()
            
            logger.info(f"Successfully executed schema file: {schema_file}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to execute schema file: {str(e)}")
            raise
    
    def create_initial_data(self, config):
        """Create initial data and test records"""
        try:
            conn = self.create_connection(config)
            cursor = conn.cursor()
            
            # Insert sample accounts
            sample_accounts = [
                ('ACC001', 'Sample Account 1', 'PORT001', 'CLIENT001', 'INDIVIDUAL', '2020-01-01'),
                ('ACC002', 'Sample Account 2', 'PORT001', 'CLIENT001', 'JOINT', '2020-01-01'),
                ('ACC003', 'Sample Account 3', 'PORT002', 'CLIENT002', 'CORPORATE', '2020-01-01')
            ]
            
            insert_account_sql = """
            INSERT INTO accounts (account_id, account_name, portfolio_id, client_id, account_type, inception_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_id) DO NOTHING
            """
            
            for account in sample_accounts:
                cursor.execute(insert_account_sql, account)
            
            conn.commit()
            logger.info("Sample accounts created")
            
            # Create ETL processing log entry
            cursor.execute("""
                INSERT INTO etl_processing_log (
                    file_name, vendor, status, records_processed, records_inserted
                ) VALUES (
                    'initial_setup.sql', 'system', 'COMPLETED', 3, 3
                )
            """)
            
            conn.commit()
            logger.info("Initial ETL log entry created")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create initial data: {str(e)}")
            raise
    
    def verify_setup(self, config):
        """Verify that the database setup is correct"""
        try:
            conn = self.create_connection(config)
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = [
                'accounts',
                'performance_data',
                'etl_processing_log',
                'data_quality_issues',
                'reconciliation_results'
            ]
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                raise ValueError(f"Missing tables: {missing_tables}")
            
            logger.info(f"All expected tables exist: {tables}")
            
            # Check partitions
            cursor.execute("""
                SELECT schemaname, tablename, partitionschemaname, partitiontablename
                FROM pg_partitions
                WHERE schemaname = 'public'
            """)
            
            partitions = cursor.fetchall()
            logger.info(f"Partitions found: {len(partitions)}")
            
            # Check functions
            cursor.execute("""
                SELECT routine_name 
                FROM information_schema.routines 
                WHERE routine_schema = 'public' 
                AND routine_type = 'FUNCTION'
            """)
            
            functions = [row[0] for row in cursor.fetchall()]
            logger.info(f"Functions created: {functions}")
            
            # Check indexes
            cursor.execute("""
                SELECT indexname, tablename 
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname
            """)
            
            indexes = cursor.fetchall()
            logger.info(f"Indexes created: {len(indexes)}")
            
            # Test sample data
            cursor.execute("SELECT COUNT(*) FROM accounts")
            account_count = cursor.fetchone()[0]
            logger.info(f"Sample accounts: {account_count}")
            
            cursor.close()
            conn.close()
            
            logger.info("Database setup verification completed successfully")
            
        except Exception as e:
            logger.error(f"Database setup verification failed: {str(e)}")
            raise
    
    def setup_database(self):
        """Main setup function"""
        try:
            logger.info("Starting database setup...")
            
            # Get database configuration
            config = self.get_database_config()
            logger.info(f"Database config: {config['host']}:{config['port']}")
            
            # Create database if needed
            self.create_database_if_not_exists(config)
            
            # Execute schema file
            schema_file = os.path.join(os.path.dirname(__file__), '..', 'sql', 'schema.sql')
            if not os.path.exists(schema_file):
                raise FileNotFoundError(f"Schema file not found: {schema_file}")
            
            self.execute_schema_file(config, schema_file)
            
            # Create initial data
            self.create_initial_data(config)
            
            # Verify setup
            self.verify_setup(config)
            
            logger.info("Database setup completed successfully!")
            
        except Exception as e:
            logger.error(f"Database setup failed: {str(e)}")
            raise

def main():
    """Main function"""
    try:
        db_setup = DatabaseSetup()
        db_setup.setup_database()
        
        print("✅ Database setup completed successfully!")
        print("\nNext steps:")
        print("1. Upload data files to the S3 raw data bucket")
        print("2. Monitor pipeline execution in AWS console")
        print("3. Check database for processed results")
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
