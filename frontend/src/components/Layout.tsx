import { ReactNode, useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Layout as AntLayout, Menu, theme, Space, Grid, Drawer, Button } from 'antd'
import { VideoCameraOutlined, UnorderedListOutlined, BarChartOutlined, SettingOutlined, MenuOutlined } from '@ant-design/icons'
import ThemeToggle from './ThemeToggle'
import Clock from './Clock'

const { Header, Content } = AntLayout

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { token } = theme.useToken()
  const screens = Grid.useBreakpoint()
  const isMobile = !screens.md
  const [navOpen, setNavOpen] = useState(false)

  const selectedKeys = useMemo(() => {
    if (location.pathname.startsWith('/giam-sat')) return ['giam-sat']
    if (location.pathname.startsWith('/vi-pham')) return ['vi-pham']
    if (location.pathname.startsWith('/bao-cao')) return ['bao-cao']
    if (location.pathname.startsWith('/cau-hinh')) return ['cau-hinh']
    return []
  }, [location.pathname])

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      {/* Header dính + nền bán trong suốt để tạo chiều sâu, không đổi cấu trúc */}
      <Header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, paddingInline: 16, flexWrap: 'nowrap' }}>
        {isMobile && (
          <Button aria-label="Mở menu" icon={<MenuOutlined />} onClick={() => setNavOpen(true)} />
        )}
        {/* Logo PNG trong public để đồng nhất favicon và header */}
        <Link
          to="/giam-sat"
          className="brand-logo"
          style={{
            borderRight: `1px solid ${token.colorBorder}`,
            paddingRight: 12,
            marginRight: 4,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            minWidth: 0,
          }}
        >
          {/* Cố định chiều cao, giữ tỉ lệ ảnh để không bị méo; thu nhỏ trên mobile */}
          <img src="/logo.png" alt="logo" style={{ height: isMobile ? 32 : 55, width: 'auto', objectFit: 'contain', display: 'block', flexShrink: 0 }} />
          {/* Ẩn chữ tiêu đề trên mobile để nhường chỗ cho đồng hồ */}
          {!isMobile && <span>AI Vision Giao Thông</span>}
        </Link>
        {!isMobile && (
          <Menu
            mode="horizontal"
            selectedKeys={selectedKeys}
            onClick={(e) => navigate(`/${e.key}`)}
            items={[
              { key: 'giam-sat', icon: <VideoCameraOutlined />, label: 'Giám sát trực tiếp' },
              { key: 'vi-pham', icon: <UnorderedListOutlined />, label: 'Danh sách' },
              { key: 'bao-cao', icon: <BarChartOutlined />, label: 'Báo cáo' },
              { key: 'cau-hinh', icon: <SettingOutlined />, label: 'Cấu hình' },
            ]}
            style={{ flex: 1, minWidth: 320 }}
          />
        )}
        <Space size={12} style={{ flexShrink: 0 }}>
          <Clock />
          <ThemeToggle />
        </Space>
      </Header>
      <Drawer
        open={navOpen}
        onClose={() => setNavOpen(false)}
        placement="left"
        width={300}
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src="/logo.png" alt="logo" style={{ height: 22, width: 'auto' }} />
            <span style={{ fontWeight: 700 }}>Menu</span>
          </div>
        }
        styles={{ header: { background: token.colorBgContainer, borderBottom: `1px solid ${token.colorBorder}` }, body: { padding: 0, background: token.colorBgContainer } }}
      >
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          onClick={(e) => { setNavOpen(false); navigate(`/${e.key}`) }}
          items={[
            { key: 'giam-sat', icon: <VideoCameraOutlined />, label: 'Giám sát trực tiếp' },
            { key: 'vi-pham', icon: <UnorderedListOutlined />, label: 'Danh sách' },
            { key: 'bao-cao', icon: <BarChartOutlined />, label: 'Báo cáo' },
            { key: 'cau-hinh', icon: <SettingOutlined />, label: 'Cấu hình' },
          ]}
          style={{ borderInlineEnd: 'none', padding: 8 }}
        />
      </Drawer>
      <Content style={{ margin: 0 }}>
        <div className="app-container">{children}</div>
      </Content>
    </AntLayout>
  )
}
