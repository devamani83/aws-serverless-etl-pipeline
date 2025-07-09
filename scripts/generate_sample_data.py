"""
Generate sample advisory performance data for testing
Creates realistic sample data for different vendors with various formats
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import random
from decimal import Decimal, ROUND_HALF_UP

class SampleDataGenerator:
    """Generates sample advisory performance data"""
    
    def __init__(self):
        self.base_date = datetime(2024, 1, 1)
        self.vendors = ['vendor_a', 'vendor_b', 'vendor_c']
        self.account_ids = [f"ACC{str(i).zfill(4)}" for i in range(1, 101)]
        self.portfolio_ids = [f"PORT{str(i).zfill(3)}" for i in range(1, 21)]
        
    def generate_account_data(self, account_id, as_of_date, previous_data=None):
        """Generate performance data for a single account"""
        
        # Base market value
        if previous_data is None:
            beginning_mv = random.uniform(50000, 2000000)
        else:
            beginning_mv = previous_data['ending_market_value']
        
        # Generate cash flows
        contributions = random.uniform(0, beginning_mv * 0.1) if random.random() > 0.7 else 0
        distributions = random.uniform(0, beginning_mv * 0.05) if random.random() > 0.8 else 0
        
        # Generate performance components
        market_return = random.uniform(-0.15, 0.20)  # -15% to +20% annual return
        monthly_return = market_return / 12
        
        income = beginning_mv * random.uniform(0.001, 0.005)  # 1.2% to 6% annual yield
        appreciation = beginning_mv * monthly_return
        fees = beginning_mv * random.uniform(0.0005, 0.002)  # 0.6% to 2.4% annual fees
        other_adjustments = random.uniform(-1000, 1000) if random.random() > 0.9 else 0
        
        # Calculate ending market value
        net_flow = contributions - distributions
        ending_mv = beginning_mv + net_flow + income + appreciation - fees + other_adjustments
        
        # Calculate TWRR (simplified)
        adjusted_beginning = beginning_mv + (net_flow / 2)  # Mid-period assumption
        twrr = (ending_mv - adjusted_beginning) / adjusted_beginning if adjusted_beginning > 0 else 0
        
        # Add some variance to vendor TWRR
        vendor_twrr = twrr + random.uniform(-0.0002, 0.0002)  # Small variance
        
        # Benchmark return
        benchmark_return = market_return / 12 + random.uniform(-0.01, 0.01)
        
        return {
            'account_id': account_id,
            'account_name': f'Account {account_id}',
            'portfolio_id': random.choice(self.portfolio_ids),
            'as_of_date': as_of_date.strftime('%Y-%m-%d'),
            'beginning_market_value': round(beginning_mv, 2),
            'contributions': round(contributions, 2),
            'distributions': round(distributions, 2),
            'income': round(income, 2),
            'appreciation': round(appreciation, 2),
            'fees': round(fees, 2),
            'other_adjustments': round(other_adjustments, 2),
            'ending_market_value': round(ending_mv, 2),
            'benchmark_return': round(benchmark_return, 6),
            'vendor_twrr': round(vendor_twrr, 6)
        }
    
    def generate_vendor_a_data(self, num_accounts=50, num_months=12):
        """Generate CSV data for Vendor A"""
        data = []
        account_history = {}
        
        for month in range(num_months):
            month_date = self.base_date + timedelta(days=30 * month)
            
            for account_id in random.sample(self.account_ids, num_accounts):
                previous_data = account_history.get(account_id)
                account_data = self.generate_account_data(account_id, month_date, previous_data)
                
                # Vendor A specific field names
                vendor_data = {
                    'acct_id': account_data['account_id'],
                    'acct_name': account_data['account_name'],
                    'port_id': account_data['portfolio_id'],
                    'report_date': account_data['as_of_date'],
                    'beginning_mv': account_data['beginning_market_value'],
                    'deposits': account_data['contributions'],
                    'withdrawals': account_data['distributions'],
                    'dividend': account_data['income'],
                    'unrealized_gl': account_data['appreciation'],
                    'management_fee': account_data['fees'],
                    'adjustments': account_data['other_adjustments'],
                    'ending_mv': account_data['ending_market_value'],
                    'bmk_return': account_data['benchmark_return'],
                    'twr': account_data['vendor_twrr']
                }
                
                data.append(vendor_data)
                account_history[account_id] = account_data
        
        # Create DataFrame and save as CSV
        df = pd.DataFrame(data)
        
        # Add some data quality issues for testing
        # Missing values
        df.loc[random.sample(range(len(df)), k=5), 'dividend'] = np.nan
        # Outliers
        df.loc[random.sample(range(len(df)), k=3), 'twr'] = df['twr'] * 10
        
        return df
    
    def generate_vendor_b_data(self, num_accounts=40, num_months=12):
        """Generate Excel data for Vendor B"""
        data = []
        account_history = {}
        
        for month in range(num_months):
            month_date = self.base_date + timedelta(days=30 * month)
            
            for account_id in random.sample(self.account_ids, num_accounts):
                previous_data = account_history.get(account_id)
                account_data = self.generate_account_data(account_id, month_date, previous_data)
                
                # Vendor B specific field names
                vendor_data = {
                    'account_number': account_data['account_id'],
                    'account_desc': account_data['account_name'],
                    'portfolio_number': account_data['portfolio_id'],
                    'date': account_data['as_of_date'],
                    'start_value': account_data['beginning_market_value'],
                    'cash_in': account_data['contributions'],
                    'cash_out': account_data['distributions'],
                    'interest': account_data['income'],
                    'price_change': account_data['appreciation'],
                    'expenses': account_data['fees'],
                    'other': account_data['other_adjustments'],
                    'end_value': account_data['ending_market_value'],
                    'index_return': account_data['benchmark_return'],
                    'time_weighted_return': account_data['vendor_twrr']
                }
                
                data.append(vendor_data)
                account_history[account_id] = account_data
        
        df = pd.DataFrame(data)
        
        # Add some data quality issues
        # Date format variations
        df.loc[0:10, 'date'] = pd.to_datetime(df.loc[0:10, 'date']).dt.strftime('%m/%d/%Y')
        
        return df
    
    def generate_vendor_c_data(self, num_accounts=30, num_months=12):
        """Generate JSON data for Vendor C"""
        data = []
        account_history = {}
        
        for month in range(num_months):
            month_date = self.base_date + timedelta(days=30 * month)
            
            for account_id in random.sample(self.account_ids, num_accounts):
                previous_data = account_history.get(account_id)
                account_data = self.generate_account_data(account_id, month_date, previous_data)
                
                # Vendor C specific structure (nested JSON)
                vendor_data = {
                    'account': {
                        'id': account_data['account_id'],
                        'name': account_data['account_name'],
                        'portfolio': account_data['portfolio_id']
                    },
                    'reporting': {
                        'period_end': account_data['as_of_date'],
                        'market_values': {
                            'beginning': account_data['beginning_market_value'],
                            'ending': account_data['ending_market_value']
                        },
                        'cash_flows': {
                            'contributions': account_data['contributions'],
                            'distributions': account_data['distributions']
                        },
                        'performance': {
                            'income_earned': account_data['income'],
                            'capital_appreciation': account_data['appreciation'],
                            'fees_paid': account_data['fees'],
                            'other_adjustments': account_data['other_adjustments']
                        },
                        'returns': {
                            'time_weighted': account_data['vendor_twrr'],
                            'benchmark': account_data['benchmark_return']
                        }
                    }
                }
                
                data.append(vendor_data)
                account_history[account_id] = account_data
        
        return data
    
    def save_sample_files(self, output_dir='sample_data'):
        """Generate and save sample files for all vendors"""
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print("Generating sample data files...")
        
        # Generate Vendor A data (CSV)
        print("Generating Vendor A data (CSV)...")
        vendor_a_data = self.generate_vendor_a_data()
        vendor_a_file = os.path.join(output_dir, f'vendor_a_performance_{datetime.now().strftime("%Y%m%d")}.csv')
        vendor_a_data.to_csv(vendor_a_file, index=False)
        print(f"Created: {vendor_a_file}")
        
        # Generate Vendor B data (Excel)
        print("Generating Vendor B data (Excel)...")
        vendor_b_data = self.generate_vendor_b_data()
        vendor_b_file = os.path.join(output_dir, f'vendor_b_performance_{datetime.now().strftime("%Y%m%d")}.xlsx')
        vendor_b_data.to_excel(vendor_b_file, index=False)
        print(f"Created: {vendor_b_file}")
        
        # Generate Vendor C data (JSON)
        print("Generating Vendor C data (JSON)...")
        vendor_c_data = self.generate_vendor_c_data()
        vendor_c_file = os.path.join(output_dir, f'vendor_c_performance_{datetime.now().strftime("%Y%m%d")}.json')
        with open(vendor_c_file, 'w') as f:
            json.dump(vendor_c_data, f, indent=2)
        print(f"Created: {vendor_c_file}")
        
        # Generate summary report
        self.generate_summary_report(vendor_a_data, vendor_b_data, vendor_c_data, output_dir)
        
        print(f"\n✅ Sample data generation completed!")
        print(f"Files saved to: {output_dir}")
        print(f"Total records: {len(vendor_a_data) + len(vendor_b_data) + len(vendor_c_data)}")
    
    def generate_summary_report(self, vendor_a_data, vendor_b_data, vendor_c_data, output_dir):
        """Generate a summary report of the sample data"""
        
        summary = {
            'generation_date': datetime.now().isoformat(),
            'vendor_summary': {
                'vendor_a': {
                    'records': len(vendor_a_data),
                    'format': 'CSV',
                    'accounts': vendor_a_data['acct_id'].nunique(),
                    'date_range': f"{vendor_a_data['report_date'].min()} to {vendor_a_data['report_date'].max()}",
                    'total_market_value': float(vendor_a_data['ending_mv'].sum()),
                    'avg_twrr': float(vendor_a_data['twr'].mean())
                },
                'vendor_b': {
                    'records': len(vendor_b_data),
                    'format': 'Excel',
                    'accounts': vendor_b_data['account_number'].nunique(),
                    'date_range': f"{vendor_b_data['date'].min()} to {vendor_b_data['date'].max()}",
                    'total_market_value': float(vendor_b_data['end_value'].sum()),
                    'avg_twrr': float(vendor_b_data['time_weighted_return'].mean())
                },
                'vendor_c': {
                    'records': len(vendor_c_data),
                    'format': 'JSON',
                    'accounts': len(set([record['account']['id'] for record in vendor_c_data])),
                    'total_market_value': sum([record['reporting']['market_values']['ending'] for record in vendor_c_data]),
                    'avg_twrr': sum([record['reporting']['returns']['time_weighted'] for record in vendor_c_data]) / len(vendor_c_data)
                }
            },
            'data_quality_issues': {
                'vendor_a': {
                    'missing_dividend_records': int(vendor_a_data['dividend'].isna().sum()),
                    'twrr_outliers': int((abs(vendor_a_data['twr']) > 0.5).sum())
                },
                'vendor_b': {
                    'date_format_variations': 'MM/DD/YYYY format in first 10 records'
                },
                'vendor_c': {
                    'nested_structure': 'Complex JSON structure with nested objects'
                }
            }
        }
        
        summary_file = os.path.join(output_dir, 'sample_data_summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Created summary report: {summary_file}")

def main():
    """Main function"""
    generator = SampleDataGenerator()
    generator.save_sample_files()

if __name__ == "__main__":
    main()
