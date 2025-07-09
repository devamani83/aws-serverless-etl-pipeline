"""
Lambda function to orchestrate the ETL pipeline
Triggered by S3 events when new files are uploaded
"""

import json
import boto3
import logging
import os
from datetime import datetime
from urllib.parse import unquote_plus

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class ETLOrchestrator:
    """Orchestrates the ETL pipeline execution"""
    
    def __init__(self):
        self.glue_client = boto3.client('glue')
        self.stepfunctions_client = boto3.client('stepfunctions')
        self.s3_client = boto3.client('s3')
        
        # Environment variables
        self.glue_job_name = os.environ.get('GLUE_JOB_NAME', 'advisory-performance-etl')
        self.step_function_arn = os.environ.get('STEP_FUNCTION_ARN')
        self.config_path = os.environ.get('CONFIG_PATH', 's3://advisory-etl-config/environment.json')
        
    def determine_vendor(self, file_name):
        """Determine vendor based on file naming pattern"""
        file_name_lower = file_name.lower()
        
        vendor_patterns = {
            'vendor_a': ['vendor_a_', 'vendora_', 'va_'],
            'vendor_b': ['vendor_b_', 'vendorb_', 'vb_'],
            'vendor_c': ['vendor_c_', 'vendorc_', 'vc_']
        }
        
        for vendor, patterns in vendor_patterns.items():
            for pattern in patterns:
                if pattern in file_name_lower:
                    return vendor
        
        # Default vendor if pattern not recognized
        logger.warning(f"Could not determine vendor for file: {file_name}, using default")
        return 'vendor_a'
    
    def validate_file_format(self, file_name, vendor):
        """Validate that file format matches vendor expectations"""
        file_extension = file_name.split('.')[-1].lower()
        
        expected_formats = {
            'vendor_a': ['csv'],
            'vendor_b': ['xlsx', 'xls'],
            'vendor_c': ['json']
        }
        
        return file_extension in expected_formats.get(vendor, [])
    
    def check_file_readiness(self, bucket, key):
        """Check if file is fully uploaded and ready for processing"""
        try:
            # Get file metadata
            response = self.s3_client.head_object(Bucket=bucket, Key=key)
            
            # Check if file has been fully uploaded (not in multipart upload)
            if 'UploadId' in response:
                logger.info(f"File {key} is still being uploaded")
                return False
            
            # Check file size (must be > 0)
            file_size = response.get('ContentLength', 0)
            if file_size == 0:
                logger.warning(f"File {key} is empty")
                return False
            
            logger.info(f"File {key} is ready for processing (size: {file_size} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Error checking file readiness: {str(e)}")
            return False
    
    def start_glue_job(self, input_path, vendor):
        """Start AWS Glue ETL job"""
        try:
            job_run_id = self.glue_client.start_job_run(
                JobName=self.glue_job_name,
                Arguments={
                    '--input_path': input_path,
                    '--vendor': vendor,
                    '--config_path': self.config_path,
                    '--enable-continuous-cloudwatch-log': 'true',
                    '--enable-metrics': 'true'
                }
            )
            
            logger.info(f"Started Glue job {self.glue_job_name} with run ID: {job_run_id['JobRunId']}")
            return job_run_id['JobRunId']
            
        except Exception as e:
            logger.error(f"Failed to start Glue job: {str(e)}")
            raise
    
    def start_step_function(self, input_path, vendor, file_name):
        """Start Step Function workflow for comprehensive processing"""
        try:
            execution_input = {
                "input_path": input_path,
                "vendor": vendor,
                "file_name": file_name,
                "config_path": self.config_path,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            execution_name = f"etl-{vendor}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            response = self.stepfunctions_client.start_execution(
                stateMachineArn=self.step_function_arn,
                name=execution_name,
                input=json.dumps(execution_input)
            )
            
            logger.info(f"Started Step Function execution: {response['executionArn']}")
            return response['executionArn']
            
        except Exception as e:
            logger.error(f"Failed to start Step Function: {str(e)}")
            raise
    
    def move_file_to_processing(self, bucket, key):
        """Move file to processing folder"""
        try:
            # Create processing key
            processing_key = f"processing/{key}"
            
            # Copy file to processing folder
            copy_source = {'Bucket': bucket, 'Key': key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=bucket,
                Key=processing_key
            )
            
            # Delete original file
            self.s3_client.delete_object(Bucket=bucket, Key=key)
            
            logger.info(f"Moved file from {key} to {processing_key}")
            return f"s3://{bucket}/{processing_key}"
            
        except Exception as e:
            logger.error(f"Failed to move file: {str(e)}")
            raise
    
    def send_notification(self, message, subject="ETL Pipeline Notification"):
        """Send notification about pipeline status"""
        try:
            sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
            if sns_topic_arn:
                sns_client = boto3.client('sns')
                sns_client.publish(
                    TopicArn=sns_topic_arn,
                    Subject=subject,
                    Message=message
                )
                logger.info("Notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
    
    def process_s3_event(self, event_record):
        """Process a single S3 event record"""
        try:
            # Extract S3 information
            bucket = event_record['s3']['bucket']['name']
            key = unquote_plus(event_record['s3']['object']['key'])
            file_name = key.split('/')[-1]
            
            logger.info(f"Processing file: s3://{bucket}/{key}")
            
            # Skip if file is in processing or archive folders
            if key.startswith(('processing/', 'archive/', 'error/')):
                logger.info(f"Skipping file in {key.split('/')[0]} folder")
                return
            
            # Check file readiness
            if not self.check_file_readiness(bucket, key):
                logger.warning(f"File {key} is not ready for processing")
                return
            
            # Determine vendor
            vendor = self.determine_vendor(file_name)
            
            # Validate file format
            if not self.validate_file_format(file_name, vendor):
                error_msg = f"Invalid file format for vendor {vendor}: {file_name}"
                logger.error(error_msg)
                self.send_notification(error_msg, "ETL Pipeline Error")
                return
            
            # Move file to processing folder
            processing_path = self.move_file_to_processing(bucket, key)
            
            # Start processing workflow
            if self.step_function_arn:
                # Use Step Functions for comprehensive workflow
                execution_arn = self.start_step_function(processing_path, vendor, file_name)
                
                # Send success notification
                success_msg = f"Started processing for file: {file_name}\nVendor: {vendor}\nExecution: {execution_arn}"
                self.send_notification(success_msg, "ETL Pipeline Started")
                
            else:
                # Direct Glue job execution
                job_run_id = self.start_glue_job(processing_path, vendor)
                
                # Send success notification
                success_msg = f"Started Glue job for file: {file_name}\nVendor: {vendor}\nJob Run ID: {job_run_id}"
                self.send_notification(success_msg, "ETL Job Started")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Processing started successfully',
                    'file': file_name,
                    'vendor': vendor
                })
            }
            
        except Exception as e:
            error_msg = f"Failed to process S3 event: {str(e)}"
            logger.error(error_msg)
            self.send_notification(error_msg, "ETL Pipeline Error")
            raise

def lambda_handler(event, context):
    """Lambda handler function"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    orchestrator = ETLOrchestrator()
    results = []
    
    try:
        # Process S3 events
        if 'Records' in event:
            for record in event['Records']:
                if record.get('eventSource') == 'aws:s3':
                    result = orchestrator.process_s3_event(record)
                    if result:
                        results.append(result)
        
        # Handle direct invocation for testing
        elif 'test_file' in event:
            # Manual test execution
            test_record = {
                's3': {
                    'bucket': {'name': event['bucket']},
                    'object': {'key': event['test_file']}
                }
            }
            result = orchestrator.process_s3_event(test_record)
            results.append(result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Lambda execution completed',
                'processed_files': len(results),
                'results': results
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution failed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'message': 'Lambda execution failed'
            })
        }
