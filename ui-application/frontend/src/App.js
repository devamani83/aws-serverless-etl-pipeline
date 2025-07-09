import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import VendorList from './pages/VendorList';
import FileDetails from './pages/FileDetails';
import ReconciliationResults from './pages/ReconciliationResults';
import AccountView from './pages/AccountView';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sidebar />
        <Layout>
          <Content style={{ margin: '16px' }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/vendors" element={<VendorList />} />
              <Route path="/files/:fileName" element={<FileDetails />} />
              <Route path="/reconciliation" element={<ReconciliationResults />} />
              <Route path="/accounts" element={<AccountView />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
