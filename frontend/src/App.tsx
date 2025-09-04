import { Route, Routes, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import LiveMonitor from './pages/LiveMonitor'
import Violations from './pages/Violations'
import Reports from './pages/Reports'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <>
      <Toaster position="top-right" />
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/giam-sat" replace />} />
          <Route path="/giam-sat" element={<LiveMonitor />} />
          <Route path="/vi-pham" element={<Violations />} />
          {/* Bỏ bản đồ */}
          <Route path="/bao-cao" element={<Reports />} />
          <Route path="/cau-hinh" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Layout>
    </>
  )
}
