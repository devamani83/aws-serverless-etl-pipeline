import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, Button, Input, Alert, Spin, Tag, Space } from 'antd';
import { SearchOutlined, DatabaseOutlined, FileTextOutlined, CalendarOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';
import moment from 'moment';

const { Search } = Input;

const VendorList = () => {
  const [loading, setLoading] = useState(false);
  const [vendors, setVendors] = useState([]);
  const [files, setFiles] = useState([]);
  const [filteredFiles, setFilteredFiles] = useState([]);
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchVendors();
  }, []);

  useEffect(() => {
    if (selectedVendor) {
      fetchFiles(selectedVendor);
    }
  }, [selectedVendor]);

  useEffect(() => {
    if (searchText) {
      const filtered = files.filter(file =>
        file.file_name.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredFiles(filtered);
    } else {
      setFilteredFiles(files);
    }
  }, [searchText, files]);

  const fetchVendors = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getVendors();
      setVendors(response.data);
      
      // Select first vendor by default
      if (response.data.length > 0) {
        setSelectedVendor(response.data[0].vendor_name);
      }
    } catch (err) {
      console.error('Failed to fetch vendors:', err);
      setError('Failed to load vendors. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchFiles = async (vendor) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await apiService.getFiles({ vendor, limit: 100 });
      setFiles(response.data);
      setFilteredFiles(response.data);
    } catch (err) {
      console.error('Failed to fetch files:', err);
      setError('Failed to load files. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVendorSelect = (vendor) => {
    setSelectedVendor(vendor);
    setSearchText('');
  };

  const handleFileClick = (fileName, vendor) => {
    navigate(`/files/${fileName}?vendor=${vendor}`);
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

  const vendorColumns = [
    {
      title: 'Vendor Name',
      dataIndex: 'vendor_name',
      key: 'vendor_name',
      render: (text) => (
        <Button 
          type="link" 
          onClick={() => handleVendorSelect(text)}
          style={{ 
            fontWeight: selectedVendor === text ? 'bold' : 'normal',
            color: selectedVendor === text ? '#1890ff' : undefined
          }}
        >
          <DatabaseOutlined style={{ marginRight: 8 }} />
          {text}
        </Button>
      ),
    },
    {
      title: 'Files Processed',
      dataIndex: 'file_count',
      key: 'file_count',
      sorter: (a, b) => a.file_count - b.file_count,
    },
    {
      title: 'Last Processed',
      dataIndex: 'last_processed',
      key: 'last_processed',
      render: (date) => date ? moment(date).format('MMM DD, YYYY HH:mm') : 'N/A',
      sorter: (a, b) => moment(a.last_processed).unix() - moment(b.last_processed).unix(),
    },
  ];

  const fileColumns = [
    {
      title: 'File Name',
      dataIndex: 'file_name',
      key: 'file_name',
      render: (text, record) => (
        <Button 
          type="link" 
          onClick={() => handleFileClick(text, record.vendor)}
          style={{ textAlign: 'left', padding: 0 }}
        >
          <FileTextOutlined style={{ marginRight: 8 }} />
          {text}
        </Button>
      ),
    },
    {
      title: 'Records',
      dataIndex: 'record_count',
      key: 'record_count',
      sorter: (a, b) => a.record_count - b.record_count,
      render: (count) => count?.toLocaleString() || 0,
    },
    {
      title: 'Status',
      dataIndex: 'overall_status',
      key: 'overall_status',
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
      onFilter: (value, record) => record.overall_status === value,
    },
    {
      title: 'Processing Started',
      dataIndex: 'processing_start',
      key: 'processing_start',
      render: (date) => date ? moment(date).format('MMM DD, YYYY HH:mm') : 'N/A',
      sorter: (a, b) => moment(a.processing_start).unix() - moment(b.processing_start).unix(),
    },
    {
      title: 'Last Updated',
      dataIndex: 'last_updated',
      key: 'last_updated',
      render: (date) => date ? moment(date).format('MMM DD, YYYY HH:mm') : 'N/A',
      sorter: (a, b) => moment(a.last_updated).unix() - moment(b.last_updated).unix(),
    },
  ];

  if (loading && vendors.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <h1 style={{ margin: 0 }}>Vendor Management</h1>
        <p style={{ margin: 0, color: '#666' }}>
          View vendor data sources and processed files
        </p>
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

      <Row gutter={[16, 16]}>
        {/* Vendor List */}
        <Col xs={24} lg={8}>
          <Card title="Data Vendors" className="summary-section">
            <Table
              columns={vendorColumns}
              dataSource={vendors}
              rowKey="vendor_name"
              pagination={false}
              size="small"
              showHeader={false}
            />
          </Card>
        </Col>

        {/* File List */}
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space>
                <span>Files from {selectedVendor || 'All Vendors'}</span>
                <Search
                  placeholder="Search files..."
                  allowClear
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ width: 300 }}
                  prefix={<SearchOutlined />}
                />
              </Space>
            }
            className="summary-section"
            loading={loading}
          >
            <Table
              columns={fileColumns}
              dataSource={filteredFiles}
              rowKey={(record) => `${record.file_name}-${record.vendor}`}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} files`,
              }}
              size="small"
            />
          </Card>
        </Col>
      </Row>

      {/* Summary Cards */}
      {selectedVendor && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} sm={8}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                    {filteredFiles.length}
                  </div>
                  <div style={{ color: '#666' }}>Total Files</div>
                </div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <DatabaseOutlined style={{ fontSize: 24, color: '#52c41a' }} />
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                    {filteredFiles.reduce((sum, file) => sum + (file.record_count || 0), 0).toLocaleString()}
                  </div>
                  <div style={{ color: '#666' }}>Total Records</div>
                </div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card>
              <div style={{ textAlign: 'center' }}>
                <CalendarOutlined style={{ fontSize: 24, color: '#722ed1' }} />
                <div style={{ marginTop: 8 }}>
                  <div style={{ fontSize: 24, fontWeight: 'bold' }}>
                    {filteredFiles.filter(f => f.overall_status === 'COMPLETED').length}
                  </div>
                  <div style={{ color: '#666' }}>Completed Files</div>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default VendorList;
