"""
AWS Glue ETL Job for Advisory Performance Data Processing
This job processes multi-vendor advisory performance data with financial calculations
"""

import sys
import json
import boto3
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging

from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import DataFrame
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.sql.window import Window

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceCalculator:
    """Financial calculations for advisory performance data"""
    
    @staticmethod
    def calculate_net_flow(contributions, distributions):
        """Calculate net flow: contributions - distributions"""
        return coalesce(contributions, lit(0)) - coalesce(distributions, lit(0))
    
    @staticmethod
    def calculate_twrr_single_period(beginning_mv, ending_mv, net_flow):
        """
        Calculate Time-Weighted Rate of Return for a single period
        TWRR = (Ending MV - Net Flow) / Beginning MV - 1
        Using mid-period flow assumption for simplicity
        """
        # Avoid division by zero
        adjusted_beginning = beginning_mv + (coalesce(net_flow, lit(0)) / 2)
        
        return when(adjusted_beginning > 0, 
                   (ending_mv - adjusted_beginning) / adjusted_beginning
                   ).otherwise(lit(None))
    
    @staticmethod
    def calculate_cumulative_twrr(df, account_col="account_id", date_col="as_of_date", twrr_col="calculated_twrr"):
        """
        Calculate cumulative TWRR over time for each account
        Cumulative TWRR = [(1 + R1) × (1 + R2) × ... × (1 + Rn)] - 1
        """
        window_spec = Window.partitionBy(account_col).orderBy(date_col).rowsBetween(Window.unboundedPreceding, Window.currentRow)
        
        # Add 1 to each period return and calculate cumulative product
        df_with_cumulative = df.withColumn(
            "twrr_factor", 
            coalesce(col(twrr_col), lit(0)) + 1
        ).withColumn(
            "cumulative_twrr_factor",
            exp(sum(log(col("twrr_factor"))).over(window_spec))
        ).withColumn(
            "cumulative_twrr",
            col("cumulative_twrr_factor") - 1
        ).drop("twrr_factor", "cumulative_twrr_factor")
        
        return df_with_cumulative
    
    @staticmethod
    def calculate_cumulative_net_flow(df, account_col="account_id", date_col="as_of_date", netflow_col="net_flow"):
        """Calculate cumulative net flow over time for each account"""
        window_spec = Window.partitionBy(account_col).orderBy(date_col).rowsBetween(Window.unboundedPreceding, Window.currentRow)
        
        return df.withColumn(
            "cumulative_net_flow",
            sum(coalesce(col(netflow_col), lit(0))).over(window_spec)
        )

class DataValidator:
    """Data quality validation and tolerance checking"""
    
    @staticmethod
    def validate_required_fields(df, required_fields):
        """Validate that required fields are not null"""
        conditions = [col(field).isNotNull() for field in required_fields]
        validation_condition = reduce(lambda a, b: a & b, conditions)
        
        return df.withColumn("has_required_fields", validation_condition)
    
    @staticmethod
    def check_twrr_tolerance(calculated_twrr, vendor_twrr, tolerance=0.0001):
        """Check if calculated TWRR is within tolerance of vendor TWRR"""
        variance = abs(coalesce(calculated_twrr, lit(0)) - coalesce(vendor_twrr, lit(0)))
        return variance <= tolerance, variance
    
    @staticmethod
    def validate_market_value_equation(beginning_mv, ending_mv, net_flow, income, appreciation, fees, tolerance=0.01):
        """
        Validate market value equation:
        Ending MV = Beginning MV + Net Flow + Income + Appreciation - Fees
        """
        calculated_ending = (beginning_mv + 
                            coalesce(net_flow, lit(0)) + 
                            coalesce(income, lit(0)) + 
                            coalesce(appreciation, lit(0)) - 
                            coalesce(fees, lit(0)))
        
        variance = abs(ending_mv - calculated_ending)
        return variance <= tolerance, variance

class ETLProcessor:
    """Main ETL processing class"""
    
    def __init__(self, glue_context, spark_context, job):
        self.glue_context = glue_context
        self.spark_context = spark_context
        self.job = job
        self.calculator = PerformanceCalculator()
        self.validator = DataValidator()
        
        # Initialize AWS clients
        self.s3_client = boto3.client('s3')
        self.secrets_client = boto3.client('secretsmanager')
        
    def load_config(self, config_path):
        """Load configuration from S3"""
        try:
            bucket, key = config_path.replace('s3://', '').split('/', 1)
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return json.loads(response['Body'].read())
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {str(e)}")
            raise
    
    def load_vendor_mapping(self, mapping_path):
        """Load vendor-specific field mappings"""
        try:
            bucket, key = mapping_path.replace('s3://', '').split('/', 1)
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return json.loads(response['Body'].read())
        except Exception as e:
            logger.error(f"Failed to load vendor mapping from {mapping_path}: {str(e)}")
            raise
    
    def normalize_column_names(self, df, field_mappings):
        """Normalize column names based on vendor mappings"""
        column_map = {}
        df_columns = [col.lower() for col in df.columns]
        
        for standard_field, possible_names in field_mappings.items():
            for possible_name in possible_names:
                if possible_name.lower() in df_columns:
                    original_col = df.columns[df_columns.index(possible_name.lower())]
                    column_map[original_col] = standard_field
                    break
        
        # Rename columns
        for old_name, new_name in column_map.items():
            df = df.withColumnRenamed(old_name, new_name)
        
        return df
    
    def cast_data_types(self, df, data_types):
        """Cast columns to appropriate data types"""
        for column, data_type in data_types.items():
            if column in df.columns:
                if data_type == "double":
                    df = df.withColumn(column, col(column).cast(DoubleType()))
                elif data_type == "date":
                    df = df.withColumn(column, to_date(col(column)))
                elif data_type == "string":
                    df = df.withColumn(column, col(column).cast(StringType()))
        
        return df
    
    def calculate_financial_metrics(self, df):
        """Calculate all financial metrics"""
        # Calculate net flow
        df = df.withColumn("net_flow", 
                          self.calculator.calculate_net_flow(
                              col("contributions"), 
                              col("distributions")
                          ))
        
        # Calculate TWRR for single period
        df = df.withColumn("calculated_twrr",
                          self.calculator.calculate_twrr_single_period(
                              col("beginning_market_value"),
                              col("ending_market_value"),
                              col("net_flow")
                          ))
        
        # Calculate cumulative metrics
        df = self.calculator.calculate_cumulative_twrr(df)
        df = self.calculator.calculate_cumulative_net_flow(df)
        
        return df
    
    def perform_data_validation(self, df, config):
        """Perform comprehensive data validation"""
        validation_rules = config.get("validation_rules", {})
        tolerance_thresholds = config.get("tolerance_thresholds", {})
        
        # Validate required fields
        required_fields = validation_rules.get("required_fields", [])
        df = self.validator.validate_required_fields(df, required_fields)
        
        # Check TWRR tolerance
        twrr_tolerance = tolerance_thresholds.get("twrr_tolerance", 0.0001)
        df = df.withColumn("twrr_within_tolerance",
                          when((col("calculated_twrr").isNotNull()) & (col("vendor_twrr").isNotNull()),
                               abs(col("calculated_twrr") - col("vendor_twrr")) <= twrr_tolerance
                               ).otherwise(lit(None)))
        
        df = df.withColumn("twrr_variance",
                          when((col("calculated_twrr").isNotNull()) & (col("vendor_twrr").isNotNull()),
                               abs(col("calculated_twrr") - col("vendor_twrr"))
                               ).otherwise(lit(None)))
        
        return df
    
    def prepare_for_database(self, df, file_info):
        """Prepare DataFrame for database insertion"""
        # Add metadata columns
        df = df.withColumn("data_source", lit(file_info.get("vendor", "unknown")))
        df = df.withColumn("file_name", lit(file_info.get("file_name", "")))
        df = df.withColumn("processed_by", lit("glue-etl-job"))
        df = df.withColumn("created_at", current_timestamp())
        df = df.withColumn("updated_at", current_timestamp())
        df = df.withColumn("reconciliation_status", lit("PENDING"))
        
        # Ensure all required columns exist
        required_columns = [
            "account_id", "as_of_date", "beginning_market_value", "ending_market_value",
            "contributions", "distributions", "income", "appreciation", "fees", "other_adjustments",
            "net_flow", "cumulative_net_flow", "calculated_twrr", "cumulative_twrr",
            "vendor_twrr", "benchmark_return", "twrr_within_tolerance", "twrr_variance",
            "data_source", "file_name", "processed_by", "created_at", "updated_at", "reconciliation_status"
        ]
        
        for column in required_columns:
            if column not in df.columns:
                df = df.withColumn(column, lit(None))
        
        return df.select(*required_columns)
    
    def write_to_database(self, df, connection_config):
        """Write DataFrame to PostgreSQL database"""
        try:
            # Get database password from Secrets Manager
            secret_name = connection_config["password_secret_name"]
            secret_response = self.secrets_client.get_secret_value(SecretId=secret_name)
            password = json.loads(secret_response['SecretString'])['password']
            
            # Construct JDBC URL
            jdbc_url = f"jdbc:postgresql://{connection_config['host']}:{connection_config['port']}/{connection_config['database']}"
            
            # Write to database with upsert logic
            df.write \
                .format("jdbc") \
                .option("url", jdbc_url) \
                .option("dbtable", "performance_data") \
                .option("user", connection_config["username"]) \
                .option("password", password) \
                .option("driver", "org.postgresql.Driver") \
                .mode("append") \
                .save()
            
            logger.info(f"Successfully wrote {df.count()} records to database")
            
        except Exception as e:
            logger.error(f"Failed to write to database: {str(e)}")
            raise
    
    def process_file(self, input_path, vendor_config, database_config):
        """Process a single file through the ETL pipeline"""
        try:
            logger.info(f"Processing file: {input_path}")
            
            # Extract file information
            file_name = input_path.split('/')[-1]
            vendor_name = vendor_config.get("name", "unknown")
            
            # Load vendor mapping
            mapping = self.load_vendor_mapping(vendor_config["schema_mapping"])
            
            # Read input file
            if input_path.endswith('.csv'):
                df = self.glue_context.create_dynamic_frame.from_options(
                    connection_type="s3",
                    connection_options={"paths": [input_path]},
                    format="csv",
                    format_options={"withHeader": True}
                ).toDF()
            elif input_path.endswith('.json'):
                df = self.spark_context.read.json(input_path)
            else:
                raise ValueError(f"Unsupported file format: {input_path}")
            
            logger.info(f"Loaded {df.count()} records from {input_path}")
            
            # Normalize column names
            df = self.normalize_column_names(df, mapping["field_mappings"])
            
            # Cast data types
            df = self.cast_data_types(df, mapping["data_types"])
            
            # Calculate financial metrics
            df = self.calculate_financial_metrics(df)
            
            # Perform data validation
            df = self.perform_data_validation(df, mapping)
            
            # Prepare for database
            file_info = {"vendor": vendor_name, "file_name": file_name}
            df = self.prepare_for_database(df, file_info)
            
            # Write to database
            self.write_to_database(df, database_config)
            
            # Log processing results
            total_records = df.count()
            valid_records = df.filter(col("has_required_fields") == True).count()
            
            logger.info(f"Processing completed: {total_records} total records, {valid_records} valid records")
            
            return {
                "status": "SUCCESS",
                "total_records": total_records,
                "valid_records": valid_records,
                "file_name": file_name,
                "vendor": vendor_name
            }
            
        except Exception as e:
            logger.error(f"Failed to process file {input_path}: {str(e)}")
            return {
                "status": "FAILED",
                "error": str(e),
                "file_name": input_path.split('/')[-1]
            }

def main():
    """Main function"""
    # Get job parameters
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'input_path',
        'vendor',
        'config_path'
    ])
    
    # Initialize Glue context
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    
    # Configure Spark for performance
    spark.conf.set("spark.sql.adaptive.enabled", "true")
    spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
    spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
    
    try:
        # Initialize processor
        processor = ETLProcessor(glueContext, sc, job)
        
        # Load configuration
        config = processor.load_config(args['config_path'])
        
        # Get vendor configuration
        vendor = args['vendor']
        vendor_config = config["vendors"][vendor]
        database_config = config["database"]
        
        # Process the file
        result = processor.process_file(
            args['input_path'],
            vendor_config,
            database_config
        )
        
        logger.info(f"ETL job completed with result: {result}")
        
    except Exception as e:
        logger.error(f"ETL job failed: {str(e)}")
        raise
    finally:
        job.commit()

if __name__ == "__main__":
    main()
