import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, Input, Select, Button, Alert, Spin, Tag, Modal, Space } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { SearchOutlined, EyeOutlined, BarChartOutlined, UserOutlined } from '@ant-design/icons';
import apiService from '../services/apiService';
import moment from 'moment';

const { Search } = Input;
const { Option } = Select;

const AccountView = () => {
  const [loading, setLoading] = useState(false);
  const [accounts, setAccounts] = useState([]);
  const [filteredAccounts, setFilteredAccounts] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [accountHistory, setAccountHistory] = useState([]);
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [filters, setFilters] = useState({
    vendor: null,
    search: '',
    status: null,
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchVendors();
    fetchAccounts();
  }, []);

  useEffect(() => {
    fetchAccounts();
  }, [filters, pagination.current, pagination.pageSize]);

  const fetchVendors = async () => {
    try {
      const response = await apiService.getVendors();
      setVendors(response.data);
    } catch (err) {
      console.error('Failed to fetch vendors:', err);
    }
  };

  const fetchAccounts = async () => {
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

      const response = await apiService.getAccounts(params);
      setAccounts(response.data);
      setFilteredAccounts(response.data);
      
      // Update pagination total
      setPagination(prev => ({
        ...prev,
        total: response.data.length < pagination.pageSize ? 
          (pagination.current - 1) * pagination.pageSize + response.data.length :
          pagination.current * pagination.pageSize + 1
      }));
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
      setError('Failed to load accounts. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAccountHistory = async (accountId, vendor) => {
    try {
      const response = await apiService.getAccountHistory(accountId, { 
        vendor, 
        months_back: 12 
      });
      setAccountHistory(response.data);
    } catch (err) {
      console.error('Failed to fetch account history:', err);
    }
  };

  const handleViewHistory = async (account) => {
    setSelectedAccount(account);
    setHistoryModalVisible(true);
    await fetchAccountHistory(account.account_id, account.vendor);
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
      search: '',
      status: null,
    });
    setPagination(prev => ({ ...prev, current: 1 }));
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'green';
      case 'COMPLETED_WITH_ISSUES':
        return 'orange';
      case 'PROCESSING':
        return 'blue';
      default:
        return 'default';
    }
  };

  const getTwrrStatusColor = (tolerance_check) => {
    return tolerance_check ? 'green' : 'red';
  };

  const columns = [
    {
      title: 'Account ID',
      dataIndex: 'account_id',
      key: 'account_id',
      fixed: 'left',
      width: 150,
      render: (text) => (
        <div style={{ fontWeight: 'bold' }}>
          <UserOutlined style={{ marginRight: 8 }} />
          {text}
        </div>
      ),
    },
    {
      title: 'Vendor',
      dataIndex: 'vendor',
      key: 'vendor',
      width: 120,
      filters: vendors.map(v => ({ text: v.vendor_name, value: v.vendor_name })),
      onFilter: (value, record) => record.vendor === value,
    },
    {
      title: 'As of Date',
      dataIndex: 'as_of_date',
      key: 'as_of_date',
      render: (date) => moment(date).format('MMM DD, YYYY'),
      sorter: (a, b) => moment(a.as_of_date).unix() - moment(b.as_of_date).unix(),
      width: 120,
    },
    {
      title: 'Beginning MV',
      dataIndex: 'beginning_market_value',
      key: 'beginning_market_value',
      render: (value) => formatCurrency(value),
      sorter: (a, b) => (a.beginning_market_value || 0) - (b.beginning_market_value || 0),
      width: 150,
    },
    {
      title: 'Ending MV',
      dataIndex: 'ending_market_value',
      key: 'ending_market_value',
      render: (value) => formatCurrency(value),
      sorter: (a, b) => (a.ending_market_value || 0) - (b.ending_market_value || 0),
      width: 150,
    },
    {
      title: 'Net Flow',
      dataIndex: 'net_flow',
      key: 'net_flow',
      render: (value) => {
        const color = value >= 0 ? '#52c41a' : '#ff4d4f';
        return <span style={{ color }}>{formatCurrency(value)}</span>;
      },
      sorter: (a, b) => (a.net_flow || 0) - (b.net_flow || 0),
      width: 120,
    },
    {
      title: 'Calculated TWRR',
      dataIndex: 'calculated_twrr',
      key: 'calculated_twrr',
      render: (value) => formatPercentage(value),
      sorter: (a, b) => (a.calculated_twrr || 0) - (b.calculated_twrr || 0),
      width: 140,
    },
    {
      title: 'Vendor TWRR',
      dataIndex: 'vendor_twrr',
      key: 'vendor_twrr',
      render: (value) => formatPercentage(value),
      sorter: (a, b) => (a.vendor_twrr || 0) - (b.vendor_twrr || 0),
      width: 120,
    },
    {
      title: 'TWRR Variance',
      dataIndex: 'twrr_variance',
      key: 'twrr_variance',
      render: (value) => {
        if (!value) return 'N/A';
        const color = Math.abs(value) > 0.0001 ? '#ff4d4f' : '#52c41a';
        return <span style={{ color }}>{value.toFixed(6)}</span>;
      },
      sorter: (a, b) => Math.abs(a.twrr_variance || 0) - Math.abs(b.twrr_variance || 0),
      width: 120,
    },
    {
      title: 'TWRR Status',
      dataIndex: 'twrr_tolerance_check',
      key: 'twrr_tolerance_check',
      render: (value) => (
        <Tag color={getTwrrStatusColor(value)}>
          {value ? 'PASS' : 'FAIL'}
        </Tag>
      ),
      filters: [
        { text: 'Pass', value: true },
        { text: 'Fail', value: false },
      ],
      onFilter: (value, record) => record.twrr_tolerance_check === value,
      width: 100,
    },
    {
      title: 'Status',
      dataIndex: 'reconciliation_status',
      key: 'reconciliation_status',
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status?.replace(/_/g, ' ') || 'UNKNOWN'}
        </Tag>
      ),
      filters: [
        { text: 'Completed', value: 'COMPLETED' },
        { text: 'Completed with Issues', value: 'COMPLETED_WITH_ISSUES' },
        { text: 'Processing', value: 'PROCESSING' },
      ],
      onFilter: (value, record) => record.reconciliation_status === value,
      width: 140,
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      width: 100,
      render: (_, record) => (
        <Button
          type="link"
          icon={<EyeOutlined />}
          onClick={() => handleViewHistory(record)}
          size="small"
        >
          History
        </Button>
      ),
    },
  ];

  // Prepare history chart data
  const historyChartData = accountHistory.map(record => ({
    date: moment(record.as_of_date).format('MMM DD'),
    ending_mv: record.ending_market_value || 0,
    calculated_twrr: (record.calculated_twrr || 0) * 100,
    vendor_twrr: (record.vendor_twrr || 0) * 100,
    cumulative_twrr: (record.cumulative_twrr || 0) * 100,
    net_flow: record.net_flow || 0,
  }));

  return (
    <div>
      <div className="page-header">
        <Row justify="space-between" align="middle">
          <Col>
            <h1 style={{ margin: 0 }}>Account Performance</h1>
            <p style={{ margin: 0, color: '#666' }}>
              View individual account performance data and reconciliation status
            </p>
          </Col>
          <Col>
            <Button onClick={resetFilters}>
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

      {/* Filters */}
      <Card className="filter-section">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} md={6}>
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
          <Col xs={24} sm={8} md={6}>
            <label>Status:</label>
            <Select
              placeholder="All statuses"
              value={filters.status}
              onChange={(value) => handleFilterChange('status', value)}
              style={{ width: '100%' }}
              allowClear
            >
              <Option value="COMPLETED">Completed</Option>
              <Option value="COMPLETED_WITH_ISSUES">Completed with Issues</Option>
              <Option value="PROCESSING">Processing</Option>
            </Select>
          </Col>
          <Col xs={24} sm={8} md={12}>
            <label>Search Account:</label>
            <Search
              placeholder="Search by Account ID"
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              style={{ width: '100%' }}
              allowClear
            />
          </Col>
        </Row>
      </Card>

      {/* Accounts Table */}
      <Card title="Account Performance Data" loading={loading}>
        <Table
          columns={columns}
          dataSource={filteredAccounts}
          rowKey={(record) => `${record.account_id}-${record.as_of_date}-${record.vendor}`}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} accounts`,
          }}
          onChange={handleTableChange}
          scroll={{ x: 1400 }}
          size="small"
          rowClassName={(record) => 
            !record.twrr_tolerance_check ? 'tolerance-fail' : ''
          }
        />
      </Card>

      {/* Account History Modal */}
      <Modal
        title={
          <Space>
            <BarChartOutlined />
            {selectedAccount ? `Account History: ${selectedAccount.account_id}` : 'Account History'}
          </Space>
        }
        open={historyModalVisible}
        onCancel={() => setHistoryModalVisible(false)}
        width={1000}
        footer={null}
      >
        {selectedAccount && (
          <div>
            {/* Account Summary */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col xs={24} sm={8}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 16, fontWeight: 'bold' }}>
                      {formatCurrency(selectedAccount.ending_market_value)}
                    </div>
                    <div style={{ color: '#666' }}>Current Market Value</div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 16, fontWeight: 'bold' }}>
                      {formatPercentage(selectedAccount.calculated_twrr)}
                    </div>
                    <div style={{ color: '#666' }}>Latest TWRR</div>
                  </div>
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card size="small">
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 16, fontWeight: 'bold' }}>
                      {selectedAccount.vendor}
                    </div>
                    <div style={{ color: '#666' }}>Data Source</div>
                  </div>
                </Card>
              </Col>
            </Row>

            {/* Performance Charts */}
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="Market Value Trend" size="small">
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={historyChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`} />
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                      <Line 
                        type="monotone" 
                        dataKey="ending_mv" 
                        stroke="#8884d8" 
                        strokeWidth={2}
                        name="Market Value"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
              <Col xs={24} lg={12}>
                <Card title="TWRR Comparison" size="small">
                  <ResponsiveContainer width="100%" height={250}>
                    <LineChart data={historyChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis tickFormatter={(value) => `${value.toFixed(2)}%`} />
                      <Tooltip formatter={(value) => `${value.toFixed(4)}%`} />
                      <Legend />
                      <Line 
                        type="monotone" 
                        dataKey="calculated_twrr" 
                        stroke="#8884d8" 
                        strokeWidth={2}
                        name="Calculated TWRR"
                      />
                      <Line 
                        type="monotone" 
                        dataKey="vendor_twrr" 
                        stroke="#82ca9d" 
                        strokeWidth={2}
                        name="Vendor TWRR"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
              <Col xs={24}>
                <Card title="Net Flows" size="small">
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={historyChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis tickFormatter={(value) => formatCurrency(value)} />
                      <Tooltip formatter={(value) => formatCurrency(value)} />
                      <Line 
                        type="monotone" 
                        dataKey="net_flow" 
                        stroke="#ff7300" 
                        strokeWidth={2}
                        name="Net Flow"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Card>
              </Col>
            </Row>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AccountView;
