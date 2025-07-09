import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Table, Select, DatePicker, Alert, Spin } from 'antd';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { FileTextOutlined, DatabaseOutlined, UserOutlined, DollarOutlined, CheckCircleOutlined, WarningOutlined } from '@ant-design/icons';
import apiService from '../services/apiService';
import moment from 'moment';

const { Option } = Select;
const { RangePicker } = DatePicker;

const Dashboard = () => {
  const [loading, setLoading] = useState(false);
  const [metrics, setMetrics] = useState({});
  const [dailyProcessing, setDailyProcessing] = useState([]);
  const [reconciliationSummary, setReconciliationSummary] = useState([]);
  const [timeRange, setTimeRange] = useState(7);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
  }, [timeRange]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [metricsResponse, reconciliationResponse] = await Promise.all([
        apiService.getDashboardMetrics({ days_back: timeRange }),
        apiService.getReconciliationSummary({ days_back: timeRange })
      ]);

      const data = metricsResponse.data;
      setMetrics(data.overall_metrics || {});
      setDailyProcessing(data.daily_processing || []);
      setReconciliationSummary(reconciliationResponse.data || []);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
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
    return `${(value * 100).toFixed(2)}%`;
  };

  const getStatusColor = (passRate) => {
    if (passRate >= 98) return '#52c41a';
    if (passRate >= 95) return '#faad14';
    return '#ff4d4f';
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  const reconciliationColumns = [
    {
      title: 'Field',
      dataIndex: 'field_name',
      key: 'field_name',
      render: (text) => text.replace(/_/g, ' ').toUpperCase(),
    },
    {
      title: 'Total Checks',
      dataIndex: 'total_checks',
      key: 'total_checks',
      sorter: (a, b) => a.total_checks - b.total_checks,
    },
    {
      title: 'Passed',
      dataIndex: 'passed_checks',
      key: 'passed_checks',
      render: (value) => <span style={{ color: '#52c41a' }}>{value}</span>,
    },
    {
      title: 'Failed',
      dataIndex: 'failed_checks',
      key: 'failed_checks',
      render: (value) => <span style={{ color: '#ff4d4f' }}>{value}</span>,
    },
    {
      title: 'Pass Rate',
      dataIndex: 'pass_rate',
      key: 'pass_rate',
      render: (value) => (
        <span style={{ color: getStatusColor(value) }}>
          {value?.toFixed(1)}%
        </span>
      ),
      sorter: (a, b) => a.pass_rate - b.pass_rate,
    },
    {
      title: 'Avg Variance',
      dataIndex: 'avg_variance',
      key: 'avg_variance',
      render: (value) => value?.toFixed(6) || 'N/A',
    },
  ];

  if (loading) {
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
            <h1 style={{ margin: 0 }}>Advisory ETL Dashboard</h1>
            <p style={{ margin: 0, color: '#666' }}>
              Monitor ETL pipeline performance and data quality
            </p>
          </Col>
          <Col>
            <Select
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: 200 }}
            >
              <Option value={1}>Last 24 Hours</Option>
              <Option value={7}>Last 7 Days</Option>
              <Option value={30}>Last 30 Days</Option>
              <Option value={90}>Last 90 Days</Option>
            </Select>
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

      {/* Key Metrics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Files Processed"
              value={metrics.total_files_processed || 0}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Vendors"
              value={metrics.total_vendors || 0}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Accounts"
              value={metrics.total_accounts || 0}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total AUM"
              value={formatCurrency(metrics.total_aum)}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Reconciliation Metrics */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Reconciliation Checks"
              value={metrics.total_recon_checks || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Overall Pass Rate"
              value={`${metrics.overall_pass_rate || 0}%`}
              prefix={metrics.overall_pass_rate >= 95 ? <CheckCircleOutlined /> : <WarningOutlined />}
              valueStyle={{ color: getStatusColor(metrics.overall_pass_rate) }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={8}>
          <Card>
            <Statistic
              title="Average TWRR"
              value={formatPercentage(metrics.avg_twrr)}
              valueStyle={{ color: '#13c2c2' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Daily Processing Volume" className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={dailyProcessing}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="processing_date" 
                  tickFormatter={(date) => moment(date).format('MM/DD')}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(date) => moment(date).format('MMMM DD, YYYY')}
                />
                <Legend />
                <Bar dataKey="files_processed" fill="#8884d8" name="Files Processed" />
                <Bar dataKey="records_processed" fill="#82ca9d" name="Records Processed" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Reconciliation Pass Rates by Field" className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={reconciliationSummary}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ field_name, pass_rate }) => 
                    `${field_name.replace(/_/g, ' ')}: ${pass_rate?.toFixed(1)}%`
                  }
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="pass_rate"
                >
                  {reconciliationSummary.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${value?.toFixed(1)}%`} />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Reconciliation Summary Table */}
      <Card title="Reconciliation Summary" style={{ marginTop: 24 }}>
        <Table
          columns={reconciliationColumns}
          dataSource={reconciliationSummary}
          rowKey="field_name"
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};

export default Dashboard;
