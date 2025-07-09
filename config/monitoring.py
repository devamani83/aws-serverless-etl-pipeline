"""
CloudWatch monitoring and alerting configuration for Advisory Performance ETL Pipeline
Creates comprehensive monitoring dashboards and alerts
"""

import json
from datetime import datetime, timedelta

class MonitoringConfig:
    """Configuration for CloudWatch monitoring and alerting"""
    
    def __init__(self, project_name="advisory-performance-etl"):
        self.project_name = project_name
        self.dashboard_name = f"{project_name}-dashboard"
        self.alarm_prefix = f"{project_name}-alarm"
    
    def get_dashboard_config(self):
        """Generate CloudWatch dashboard configuration"""
        dashboard_config = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Glue", "glue.driver.aggregate.numCompletedTasks", "JobName", "advisory-performance-etl"],
                            ["AWS/Glue", "glue.driver.aggregate.numFailedTasks", "JobName", "advisory-performance-etl"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Glue Job Task Status",
                        "yAxis": {
                            "left": {
                                "min": 0
                            }
                        }
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Lambda", "Duration", "FunctionName", "advisory-etl-orchestrator"],
                            ["AWS/Lambda", "Errors", "FunctionName", "advisory-etl-orchestrator"],
                            ["AWS/Lambda", "Invocations", "FunctionName", "advisory-etl-orchestrator"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Lambda Function Metrics"
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/States", "ExecutionsFailed", "StateMachineArn", "advisory-performance-etl-workflow"],
                            ["AWS/States", "ExecutionsSucceeded", "StateMachineArn", "advisory-performance-etl-workflow"],
                            ["AWS/States", "ExecutionsStarted", "StateMachineArn", "advisory-performance-etl-workflow"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Step Functions Execution Status"
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/RDS", "DatabaseConnections", "DBInstanceIdentifier", "advisory-performance-db"],
                            ["AWS/RDS", "CPUUtilization", "DBInstanceIdentifier", "advisory-performance-db"],
                            ["AWS/RDS", "ReadLatency", "DBInstanceIdentifier", "advisory-performance-db"],
                            ["AWS/RDS", "WriteLatency", "DBInstanceIdentifier", "advisory-performance-db"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "RDS Database Metrics"
                    }
                },
                {
                    "type": "log",
                    "x": 0,
                    "y": 12,
                    "width": 24,
                    "height": 6,
                    "properties": {
                        "query": "SOURCE '/aws/glue/advisory-performance-etl'\n| fields @timestamp, @message\n| filter @message like /ERROR/\n| sort @timestamp desc\n| limit 100",
                        "region": "us-east-1",
                        "title": "Recent ETL Errors",
                        "view": "table"
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 18,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/S3", "BucketSizeBytes", "BucketName", "advisory-etl-raw-data", "StorageType", "StandardStorage"],
                            ["AWS/S3", "NumberOfObjects", "BucketName", "advisory-etl-raw-data", "StorageType", "AllStorageTypes"]
                        ],
                        "period": 86400,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "S3 Storage Metrics"
                    }
                },
                {
                    "type": "number",
                    "x": 8,
                    "y": 18,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["CWAgent", "ETL_Records_Processed", "Environment", "production"],
                            ["CWAgent", "ETL_Records_Failed", "Environment", "production"]
                        ],
                        "period": 300,
                        "stat": "Sum",
                        "region": "us-east-1",
                        "title": "Data Processing Summary"
                    }
                },
                {
                    "type": "number",
                    "x": 16,
                    "y": 18,
                    "width": 8,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["CWAgent", "TWRR_Reconciliation_Pass_Rate", "Environment", "production"],
                            ["CWAgent", "Data_Quality_Score", "Environment", "production"]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": "us-east-1",
                        "title": "Data Quality Metrics"
                    }
                }
            ]
        }
        
        return dashboard_config
    
    def get_alarm_configurations(self):
        """Generate CloudWatch alarm configurations"""
        alarms = [
            {
                "AlarmName": f"{self.alarm_prefix}-glue-job-failure",
                "AlarmDescription": "Alert when Glue ETL job fails",
                "MetricName": "glue.driver.aggregate.numFailedTasks",
                "Namespace": "AWS/Glue",
                "Statistic": "Sum",
                "Period": 300,
                "EvaluationPeriods": 1,
                "Threshold": 1,
                "ComparisonOperator": "GreaterThanOrEqualToThreshold",
                "Dimensions": [
                    {
                        "Name": "JobName",
                        "Value": "advisory-performance-etl"
                    }
                ],
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:ACCOUNT_ID:advisory-etl-alerts"
                ],
                "TreatMissingData": "notBreaching"
            },
            {
                "AlarmName": f"{self.alarm_prefix}-lambda-errors",
                "AlarmDescription": "Alert when Lambda function has errors",
                "MetricName": "Errors",
                "Namespace": "AWS/Lambda",
                "Statistic": "Sum",
                "Period": 300,
                "EvaluationPeriods": 2,
                "Threshold": 3,
                "ComparisonOperator": "GreaterThanThreshold",
                "Dimensions": [
                    {
                        "Name": "FunctionName",
                        "Value": "advisory-etl-orchestrator"
                    }
                ],
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:ACCOUNT_ID:advisory-etl-alerts"
                ]
            },
            {
                "AlarmName": f"{self.alarm_prefix}-lambda-duration",
                "AlarmDescription": "Alert when Lambda function duration is too high",
                "MetricName": "Duration",
                "Namespace": "AWS/Lambda",
                "Statistic": "Average",
                "Period": 300,
                "EvaluationPeriods": 3,
                "Threshold": 240000,  # 4 minutes in milliseconds
                "ComparisonOperator": "GreaterThanThreshold",
                "Dimensions": [
                    {
                        "Name": "FunctionName",
                        "Value": "advisory-etl-orchestrator"
                    }
                ],
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:ACCOUNT_ID:advisory-etl-alerts"
                ]
            },
            {
                "AlarmName": f"{self.alarm_prefix}-stepfunctions-failures",
                "AlarmDescription": "Alert when Step Functions executions fail",
                "MetricName": "ExecutionsFailed",
                "Namespace": "AWS/States",
                "Statistic": "Sum",
                "Period": 300,
                "EvaluationPeriods": 1,
                "Threshold": 1,
                "ComparisonOperator": "GreaterThanOrEqualToThreshold",
                "Dimensions": [
                    {
                        "Name": "StateMachineArn",
                        "Value": "advisory-performance-etl-workflow"
                    }
                ],
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:ACCOUNT_ID:advisory-etl-alerts"
                ]
            },
            {
                "AlarmName": f"{self.alarm_prefix}-rds-cpu-high",
                "AlarmDescription": "Alert when RDS CPU utilization is high",
                "MetricName": "CPUUtilization",
                "Namespace": "AWS/RDS",
                "Statistic": "Average",
                "Period": 300,
                "EvaluationPeriods": 3,
                "Threshold": 80,
                "ComparisonOperator": "GreaterThanThreshold",
                "Dimensions": [
                    {
                        "Name": "DBInstanceIdentifier",
                        "Value": "advisory-performance-db"
                    }
                ],
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:ACCOUNT_ID:advisory-etl-alerts"
                ]
            },
            {
                "AlarmName": f"{self.alarm_prefix}-rds-connections-high",
                "AlarmDescription": "Alert when RDS database connections are high",
                "MetricName": "DatabaseConnections",
                "Namespace": "AWS/RDS",
                "Statistic": "Average",
                "Period": 300,
                "EvaluationPeriods": 2,
                "Threshold": 80,
                "ComparisonOperator": "GreaterThanThreshold",
                "Dimensions": [
                    {
                        "Name": "DBInstanceIdentifier",
                        "Value": "advisory-performance-db"
                    }
                ],
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:ACCOUNT_ID:advisory-etl-alerts"
                ]
            },
            {
                "AlarmName": f"{self.alarm_prefix}-data-quality-low",
                "AlarmDescription": "Alert when data quality score is below threshold",
                "MetricName": "Data_Quality_Score",
                "Namespace": "CWAgent",
                "Statistic": "Average",
                "Period": 600,
                "EvaluationPeriods": 2,
                "Threshold": 90,
                "ComparisonOperator": "LessThanThreshold",
                "Dimensions": [
                    {
                        "Name": "Environment",
                        "Value": "production"
                    }
                ],
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:ACCOUNT_ID:advisory-etl-alerts"
                ]
            },
            {
                "AlarmName": f"{self.alarm_prefix}-reconciliation-failures",
                "AlarmDescription": "Alert when TWRR reconciliation pass rate is low",
                "MetricName": "TWRR_Reconciliation_Pass_Rate",
                "Namespace": "CWAgent",
                "Statistic": "Average",
                "Period": 600,
                "EvaluationPeriods": 1,
                "Threshold": 95,
                "ComparisonOperator": "LessThanThreshold",
                "Dimensions": [
                    {
                        "Name": "Environment",
                        "Value": "production"
                    }
                ],
                "AlarmActions": [
                    "arn:aws:sns:us-east-1:ACCOUNT_ID:advisory-etl-alerts"
                ]
            }
        ]
        
        return alarms
    
    def get_custom_metrics_config(self):
        """Configuration for custom metrics to be published"""
        custom_metrics = {
            "metrics": [
                {
                    "metric_name": "ETL_Records_Processed",
                    "namespace": "CWAgent",
                    "dimensions": {"Environment": "production"},
                    "description": "Total number of records processed by ETL pipeline"
                },
                {
                    "metric_name": "ETL_Records_Failed",
                    "namespace": "CWAgent",
                    "dimensions": {"Environment": "production"},
                    "description": "Number of records that failed processing"
                },
                {
                    "metric_name": "TWRR_Reconciliation_Pass_Rate",
                    "namespace": "CWAgent",
                    "dimensions": {"Environment": "production"},
                    "description": "Percentage of TWRR values within tolerance"
                },
                {
                    "metric_name": "Data_Quality_Score",
                    "namespace": "CWAgent",
                    "dimensions": {"Environment": "production"},
                    "description": "Overall data quality score (0-100)"
                },
                {
                    "metric_name": "Pipeline_Execution_Duration",
                    "namespace": "CWAgent",
                    "dimensions": {"Environment": "production", "Vendor": "all"},
                    "description": "Total pipeline execution time in seconds"
                },
                {
                    "metric_name": "Market_Value_Reconciliation_Variance",
                    "namespace": "CWAgent",
                    "dimensions": {"Environment": "production"},
                    "description": "Average variance in market value reconciliation"
                }
            ]
        }
        
        return custom_metrics
    
    def get_log_insights_queries(self):
        """Predefined CloudWatch Log Insights queries"""
        queries = {
            "etl_errors": {
                "name": "ETL Errors Analysis",
                "query": """
                fields @timestamp, @message
                | filter @message like /ERROR/
                | stats count() by bin(5m)
                | sort @timestamp desc
                """,
                "log_groups": ["/aws/glue/advisory-performance-etl"]
            },
            "processing_performance": {
                "name": "Processing Performance",
                "query": """
                fields @timestamp, @message
                | filter @message like /records processed/
                | parse @message "processed * records"
                | stats avg(records), max(records), min(records) by bin(1h)
                """,
                "log_groups": ["/aws/glue/advisory-performance-etl"]
            },
            "reconciliation_issues": {
                "name": "Reconciliation Issues",
                "query": """
                fields @timestamp, @message
                | filter @message like /tolerance/ or @message like /variance/
                | stats count() by bin(1h)
                | sort @timestamp desc
                """,
                "log_groups": ["/aws/lambda/advisory-etl-reconciliation"]
            },
            "data_quality_trends": {
                "name": "Data Quality Trends",
                "query": """
                fields @timestamp, @message
                | filter @message like /data quality/
                | parse @message "quality score: *"
                | stats avg(score) by bin(1h)
                | sort @timestamp desc
                """,
                "log_groups": ["/aws/glue/advisory-data-quality-checker"]
            }
        }
        
        return queries
    
    def generate_monitoring_config_file(self, output_file="monitoring_config.json"):
        """Generate complete monitoring configuration file"""
        config = {
            "project_name": self.project_name,
            "dashboard": {
                "name": self.dashboard_name,
                "config": self.get_dashboard_config()
            },
            "alarms": self.get_alarm_configurations(),
            "custom_metrics": self.get_custom_metrics_config(),
            "log_insights_queries": self.get_log_insights_queries(),
            "notification_config": {
                "sns_topic": "advisory-etl-alerts",
                "email_endpoints": [
                    "data-engineering-team@company.com",
                    "etl-alerts@company.com"
                ],
                "slack_webhook": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
            },
            "retention_policies": {
                "cloudwatch_logs": "30 days",
                "custom_metrics": "90 days",
                "alarm_history": "365 days"
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config

def create_monitoring_setup():
    """Create complete monitoring setup"""
    print("Creating CloudWatch monitoring configuration...")
    
    monitoring = MonitoringConfig()
    config = monitoring.generate_monitoring_config_file()
    
    print("✅ Monitoring configuration created!")
    print("\nMonitoring Components:")
    print(f"- Dashboard: {config['dashboard']['name']}")
    print(f"- Alarms: {len(config['alarms'])}")
    print(f"- Custom Metrics: {len(config['custom_metrics']['metrics'])}")
    print(f"- Log Queries: {len(config['log_insights_queries'])}")
    
    print("\nNext Steps:")
    print("1. Deploy the monitoring configuration using AWS CLI or CDK")
    print("2. Subscribe to SNS topic for alert notifications")
    print("3. Configure Slack webhook for team notifications")
    print("4. Set up custom metric publishing in application code")
    
    return config

if __name__ == "__main__":
    create_monitoring_setup()
