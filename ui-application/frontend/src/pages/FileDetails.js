import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { Row, Col, Card, Table, Statistic, Alert, Spin, Tag, Tabs, Button, Space } from 'antd';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { 
  FileTextOutlined, 
  DollarOutlined, 
  PercentageOutlined, 
  CheckCircleOutlined, 
  ExclamationCircleOutlined,
  DownloadOutlined 
} from '@ant-design/icons';
import apiService from '../services/apiService';
import moment from 'moment';

const { TabPane } = Tabs;

const FileDetails = () => {
  const { fileName } = useParams();
  const [searchParams] = useSearchParams();
  const vendor = searchParams.get('vendor');
  
  const [loading, setLoading] = useState(false);
  const [fileDetails, setFileDetails] = useState({});
  const [sampleData, setSampleData] = useState([]);
  const [reconciliationData, setReconciliationData] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (fileName && vendor) {
      fetchFileDetails();
      fetchReconciliationData();
    }
  }, [fileName, vendor]);

  const fetchFileDetails = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getFileDetails(fileName, vendor);
      const data = response.data;
      
      setFileDetails(data.summary || {});
      setSampleData(data.sample_records || []);
    } catch (err) {
      console.error('Failed to fetch file details:', err);
      setError('Failed to load file details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchReconciliationData = async () => {
    try {
      const response = await apiService.getReconciliationResults({
        file_name: fileName,
        vendor: vendor,
        limit: 100
      });
      setReconciliationData(response.data || []);
    } catch (err) {
      console.error('Failed to fetch reconciliation data:', err);
    }
  };

  const handleExportReport = async () => {
    try {
      const response = await apiService.exportReconciliationReport(fileName, vendor);
      const data = response.data;
      
      // Create and download file
      const blob = new Blob([atob(data.data)], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = data.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export report:', err);
    }
  };

  const formatCurrency = (value) => {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (value) => {
    if (!value) return '0%';
    return `${(value * 100).toFixed(4)}%`;
  };

  const sampleDataColumns = [
    {
      title: 'Account ID',
      dataIndex: 'account_id',
      key: 'account_id',
      fixed: 'left',
      width: 150,
    },
    {
      title: 'As of Date',
      dataIndex: 'as_of_date',
      key: 'as_of_date',
      render: (date) => moment(date).format('MMM DD, YYYY'),
      width: 120,
    },
    {
      title: 'Beginning MV',
      dataIndex: 'beginning_market_value',
      key: 'beginning_market_value',
      render: (value) => formatCurrency(value),
      width: 150,
    },
    {
      title: 'Ending MV',
      dataIndex: 'ending_market_value',
      key: 'ending_market_value',
      render: (value) => formatCurrency(value),
      width: 150,
    },
    {
      title: 'Net Flow',
      dataIndex: 'net_flow',
      key: 'net_flow',
      render: (value) => formatCurrency(value),
      width: 120,
    },
    {
      title: 'Calculated TWRR',
      dataIndex: 'calculated_twrr',
      key: 'calculated_twrr',
      render: (value) => formatPercentage(value),
      width: 140,
    },
    {
      title: 'Vendor TWRR',
      dataIndex: 'vendor_twrr',
      key: 'vendor_twrr',
      render: (value) => formatPercentage(value),
      width: 120,
    },
    {
      title: 'TWRR Check',
      dataIndex: 'twrr_tolerance_check',
      key: 'twrr_tolerance_check',
      render: (value) => (
        <Tag color={value ? 'green' : 'red'}>
          {value ? 'PASS' : 'FAIL'}
        </Tag>
      ),
      width: 100,
    },
  ];

  const reconciliationColumns = [
    {
      title: 'Account ID',
      dataIndex: 'account_id',
      key: 'account_id',
      width: 150,
    },
    {
      title: 'Field',
      dataIndex: 'field_name',
      key: 'field_name',
      render: (text) => text.replace(/_/g, ' ').toUpperCase(),
      width: 120,
    },
    {
      title: 'Calculated Value',
      dataIndex: 'calculated_value',
      key: 'calculated_value',
      render: (value) => typeof value === 'number' ? value.toFixed(6) : value,
      width: 150,
    },
    {
      title: 'Vendor Value',
      dataIndex: 'vendor_value',
      key: 'vendor_value',
      render: (value) => typeof value === 'number' ? value.toFixed(6) : value,
      width: 150,
    },
    {
      title: 'Variance',
      dataIndex: 'variance',
      key: 'variance',
      render: (value) => typeof value === 'number' ? value.toFixed(6) : 'N/A',
      width: 120,
    },
    {
      title: 'Within Tolerance',
      dataIndex: 'within_tolerance',
      key: 'within_tolerance',
      render: (value) => (
        <Tag color={value ? 'green' : 'red'}>
          {value ? 'PASS' : 'FAIL'}
        </Tag>
      ),
      width: 120,
    },
  ];

  // Prepare chart data
  const chartData = sampleData.map(record => ({
    account_id: record.account_id,
    ending_mv: record.ending_market_value || 0,
    calculated_twrr: (record.calculated_twrr || 0) * 100,
    vendor_twrr: (record.vendor_twrr || 0) * 100,
  }));

  if (loading && !fileDetails.file_name) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <Row justify="space-between" align="middle">
          <Col>
            <h1 style={{ margin: 0 }}>File Details</h1>
            <p style={{ margin: 0, color: '#666' }}>
              {fileName} from {vendor}
            </p>
          </Col>
          <Col>
            <Button 
              type="primary" 
              icon={<DownloadOutlined />}
              onClick={handleExportReport}
            >
              Export Reconciliation Report
            </Button>
          </Col>
        </Row>
      </div>

      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Summary Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Records"
              value={fileDetails.total_records || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Unique Accounts"
              value={fileDetails.unique_accounts || 0}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Market Value"
              value={formatCurrency(fileDetails.total_market_value)}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Average TWRR"
              value={formatPercentage(fileDetails.avg_twrr)}
              prefix={<PercentageOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Additional File Info */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Date Range"
              value={`${moment(fileDetails.earliest_date).format('MMM DD')} - ${moment(fileDetails.latest_date).format('MMM DD, YYYY')}`}
              valueStyle={{ fontSize: 16 }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="TWRR Failures"
              value={fileDetails.twrr_failures || 0}
              prefix={fileDetails.twrr_failures > 0 ? <ExclamationCircleOutlined /> : <CheckCircleOutlined />}
              valueStyle={{ color: fileDetails.twrr_failures > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Detailed Data Tabs */}
      <Card>
        <Tabs defaultActiveKey="1">
          <TabPane tab="Sample Data" key="1">
            <Table
              columns={sampleDataColumns}
              dataSource={sampleData}
              rowKey={(record) => `${record.account_id}-${record.as_of_date}`}
              scroll={{ x: 1200 }}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
              }}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="Reconciliation Results" key="2">
            <Table
              columns={reconciliationColumns}
              dataSource={reconciliationData}
              rowKey={(record) => `${record.account_id}-${record.field_name}-${record.as_of_date}`}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
              }}
              size="small"
            />
          </TabPane>
          
          <TabPane tab="Performance Chart" key="3">
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <div className="chart-container">
                  <h3>Market Values by Account</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData.slice(0, 10)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="account_id" 
                        angle={-45}
                        textAnchor="end"
                        height={100}
                      />
                      <YAxis tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`} />
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                      <Bar dataKey="ending_mv" fill="#8884d8" name="Ending Market Value" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Col>
              <Col xs={24} lg={12}>
                <div className="chart-container">
                  <h3>TWRR Comparison</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={chartData.slice(0, 10)}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="account_id" 
                        angle={-45}
                        textAnchor="end"
                        height={100}
                      />
                      <YAxis tickFormatter={(value) => `${value.toFixed(2)}%`} />
                      <Tooltip formatter={(value) => `${value.toFixed(4)}%`} />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="calculated_twrr" 
                        stroke="#8884d8" 
                        name="Calculated TWRR"
                        strokeWidth={2}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="vendor_twrr" 
                        stroke="#82ca9d" 
                        name="Vendor TWRR"
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </Col>
            </Row>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default FileDetails;
