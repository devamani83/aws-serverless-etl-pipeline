import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, Select, Input, Button, Alert, Spin, Tag, Space, DatePicker } from 'antd';
import { SearchOutlined, FilterOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiService from '../services/apiService';
import moment from 'moment';

const { Option } = Select;
const { Search } = Input;
const { RangePicker } = DatePicker;

const ReconciliationResults = () => {
  const [loading, setLoading] = useState(false);
  const [reconciliationData, setReconciliationData] = useState([]);
  const [summaryData, setSummaryData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [filters, setFilters] = useState({
    vendor: null,
    field_name: null,
    tolerance_failures_only: false,
    account_search: '',
    date_range: null,
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchVendors();
    fetchReconciliationData();
    fetchSummaryData();
  }, []);

  useEffect(() => {
    fetchReconciliationData();
  }, [filters, pagination.current, pagination.pageSize]);

  const fetchVendors = async () => {
    try {
      const response = await apiService.getVendors();
      setVendors(response.data);
    } catch (err) {
      console.error('Failed to fetch vendors:', err);
    }
  };

  const fetchReconciliationData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        ...filters,
        limit: pagination.pageSize,
        offset: (pagination.current - 1) * pagination.pageSize,
      };
      
      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === '') {
          delete params[key];
        }
      });

      const response = await apiService.getReconciliationResults(params);
      setReconciliationData(response.data);
      setFilteredData(response.data);
      
      // Update pagination total (this would normally come from the API)
      setPagination(prev => ({
        ...prev,
        total: response.data.length < pagination.pageSize ? 
          (pagination.current - 1) * pagination.pageSize + response.data.length :
          pagination.current * pagination.pageSize + 1
      }));
    } catch (err) {
      console.error('Failed to fetch reconciliation data:', err);
      setError('Failed to load reconciliation data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSummaryData = async () => {
    try {
      const response = await apiService.getReconciliationSummary({ days_back: 30 });
      setSummaryData(response.data);
    } catch (err) {
      console.error('Failed to fetch summary data:', err);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleTableChange = (pagination) => {
    setPagination(pagination);
  };

  const resetFilters = () => {
    setFilters({
      vendor: null,
      field_name: null,
      tolerance_failures_only: false,
      account_search: '',
      date_range: null,
    });
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const getStatusColor = (within_tolerance) => {
    return within_tolerance ? 'green' : 'red';
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

  const columns = [
    {
      title: 'Account ID',
      dataIndex: 'account_id',
      key: 'account_id',
      fixed: 'left',
      width: 150,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="Search Account ID"
            value={selectedKeys[0]}
            onChange={(e) => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ width: 188, marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              Search
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              Reset
            </Button>
          </Space>
        </div>
      ),
      filterIcon: (filtered) => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
      onFilter: (value, record) =>
        record.account_id.toString().toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: 'Date',
      dataIndex: 'as_of_date',
      key: 'as_of_date',
      render: (date) => moment(date).format('MMM DD, YYYY'),
      sorter: (a, b) => moment(a.as_of_date).unix() - moment(b.as_of_date).unix(),
      width: 120,
    },
    {
      title: 'Field',
      dataIndex: 'field_name',
      key: 'field_name',
      render: (text) => text.replace(/_/g, ' ').toUpperCase(),
      filters: [
        { text: 'Market Value', value: 'ending_market_value' },
        { text: 'TWRR', value: 'twrr' },
        { text: 'Net Flow', value: 'net_flow' },
      ],
      onFilter: (value, record) => record.field_name === value,
      width: 140,
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
      render: (value) => {
        if (typeof value !== 'number') return 'N/A';
        const color = value > 0.001 ? '#ff4d4f' : '#52c41a';
        return <span style={{ color }}>{value.toFixed(6)}</span>;
      },
      sorter: (a, b) => (a.variance || 0) - (b.variance || 0),
      width: 120,
    },
    {
      title: 'Tolerance',
      dataIndex: 'tolerance_threshold',
      key: 'tolerance_threshold',
      render: (value) => typeof value === 'number' ? value.toFixed(6) : 'N/A',
      width: 120,
    },
    {
      title: 'Status',
      dataIndex: 'within_tolerance',
      key: 'within_tolerance',
      render: (value) => (
        <Tag color={getStatusColor(value)} icon={value ? <CheckCircleOutlined /> : <ExclamationCircleOutlined />}>
          {value ? 'PASS' : 'FAIL'}
        </Tag>
      ),
      filters: [
        { text: 'Pass', value: true },
        { text: 'Fail', value: false },
      ],
      onFilter: (value, record) => record.within_tolerance === value,
      width: 100,
    },
    {
      title: 'Vendor',
      dataIndex: 'vendor',
      key: 'vendor',
      filters: vendors.map(v => ({ text: v.vendor_name, value: v.vendor_name })),
      onFilter: (value, record) => record.vendor === value,
      width: 120,
    },
  ];

  // Prepare chart data
  const passFailData = summaryData.map(item => ({
    field: item.field_name.replace(/_/g, ' ').toUpperCase(),
    passed: item.passed_checks,
    failed: item.failed_checks,
    pass_rate: item.pass_rate,
  }));

  const fieldDistribution = summaryData.map(item => ({
    name: item.field_name.replace(/_/g, ' ').toUpperCase(),
    value: item.total_checks,
    pass_rate: item.pass_rate,
  }));

  return (
    <div>
      <div className="page-header">
        <Row justify="space-between" align="middle">
          <Col>
            <h1 style={{ margin: 0 }}>Reconciliation Results</h1>
            <p style={{ margin: 0, color: '#666' }}>
              Monitor tolerance checks and data quality validation
            </p>
          </Col>
          <Col>
            <Button onClick={resetFilters} icon={<FilterOutlined />}>
              Reset Filters
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

      {/* Summary Charts */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Pass/Fail by Field" className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={passFailData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="field" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="passed" stackId="a" fill="#52c41a" name="Passed" />
                <Bar dataKey="failed" stackId="a" fill="#ff4d4f" name="Failed" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Checks Distribution by Field" className="chart-container">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={fieldDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${value}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {fieldDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card className="filter-section">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} md={6}>
            <label>Vendor:</label>
            <Select
              placeholder="Select vendor"
              value={filters.vendor}
              onChange={(value) => handleFilterChange('vendor', value)}
              style={{ width: '100%' }}
              allowClear
            >
              {vendors.map(vendor => (
                <Option key={vendor.vendor_name} value={vendor.vendor_name}>
                  {vendor.vendor_name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <label>Field:</label>
            <Select
              placeholder="Select field"
              value={filters.field_name}
              onChange={(value) => handleFilterChange('field_name', value)}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="ending_market_value">Market Value</Option>
              <Option value="twrr">TWRR</Option>
              <Option value="net_flow">Net Flow</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <label>Status:</label>
            <Select
              placeholder="All results"
              value={filters.tolerance_failures_only}
              onChange={(value) => handleFilterChange('tolerance_failures_only', value)}
              style={{ width: '100%' }}
            >
              <Option value={false}>All Results</Option>
              <Option value={true}>Failures Only</Option>
            </Select>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <label>Search Account:</label>
            <Search
              placeholder="Account ID"
              value={filters.account_search}
              onChange={(e) => handleFilterChange('account_search', e.target.value)}
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
        </Row>
      </Card>

      {/* Results Table */}
      <Card title="Reconciliation Details" loading={loading}>
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey={(record) => `${record.account_id}-${record.field_name}-${record.as_of_date}`}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} reconciliation checks`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          size="small"
          rowClassName={(record) => 
            !record.within_tolerance ? 'tolerance-fail' : 'tolerance-pass'
          }
        />
      </Card>

      {/* Summary Statistics */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {summaryData.map((item, index) => (
          <Col xs={24} sm={12} lg={8} key={item.field_name}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 18, fontWeight: 'bold', marginBottom: 8 }}>
                  {item.field_name.replace(/_/g, ' ').toUpperCase()}
                </div>
                <div style={{ 
                  fontSize: 24, 
                  fontWeight: 'bold', 
                  color: item.pass_rate >= 95 ? '#52c41a' : item.pass_rate >= 90 ? '#faad14' : '#ff4d4f'
                }}>
                  {item.pass_rate?.toFixed(1)}%
                </div>
                <div style={{ color: '#666' }}>
                  {item.passed_checks} / {item.total_checks} checks passed
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default ReconciliationResults;
