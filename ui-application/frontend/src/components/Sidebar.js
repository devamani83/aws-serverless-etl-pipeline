import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  DatabaseOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  UserOutlined,
  BarChartOutlined
} from '@ant-design/icons';

const { Sider } = Layout;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/vendors',
      icon: <DatabaseOutlined />,
      label: 'Vendors',
    },
    {
      key: '/reconciliation',
      icon: <CheckCircleOutlined />,
      label: 'Reconciliation',
    },
    {
      key: '/accounts',
      icon: <UserOutlined />,
      label: 'Accounts',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Sider
      width={250}
      style={{
        background: '#001529',
      }}
    >
      <div style={{
        height: 64,
        background: '#002140',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'white',
        fontSize: '18px',
        fontWeight: 'bold'
      }}>
        Advisory ETL Monitor
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={menuItems}
        onClick={handleMenuClick}
        style={{ borderRight: 0 }}
      />
    </Sider>
  );
};

export default Sidebar;
