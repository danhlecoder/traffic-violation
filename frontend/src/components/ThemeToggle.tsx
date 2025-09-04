import { Button, Tooltip } from 'antd'
import { BulbOutlined, DesktopOutlined, MoonOutlined } from '@ant-design/icons'
import { useTheme, ThemeMode } from '../store/useTheme'

export default function ThemeToggle() {
  const mode = useTheme((s) => s.mode)
  const setMode = useTheme((s) => s.setMode)
  return (
    <div className="theme-group">
      <Tooltip title="Sáng">
        <Button
          size="small"
          shape="round"
          type={mode === 'light' ? 'primary' : 'default'}
          icon={<BulbOutlined />}
          onClick={() => setMode('light' as ThemeMode)}
        />
      </Tooltip>
      <Tooltip title="Hệ thống">
        <Button
          size="small"
          shape="round"
          type={mode === 'system' ? 'primary' : 'default'}
          icon={<DesktopOutlined />}
          onClick={() => setMode('system' as ThemeMode)}
        />
      </Tooltip>
      <Tooltip title="Tối">
        <Button
          size="small"
          shape="round"
          type={mode === 'dark' ? 'primary' : 'default'}
          icon={<MoonOutlined />}
          onClick={() => setMode('dark' as ThemeMode)}
        />
      </Tooltip>
    </div>
  )
}
