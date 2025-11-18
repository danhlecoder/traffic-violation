import { Card, Typography, Tag, Space } from 'antd'
import { ClockCircleOutlined, UserOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { useStore } from '../store/useStore'
import { violationTypeToTagColor } from '../constants/violations'

const { Text } = Typography

// Interface cho log entry
export interface LogEntry {
  id: string
  timestamp: Date
  user: string
  action: 'confirm' | 'skip'
  violationTypes: string[]
  trackId?: string
  plate: string
  camera: string
  details?: string
}

export default function OperationLog({ logs, onSelect }: { logs?: LogEntry[]; onSelect?: (payload: { trackId?: string; plate?: string; violationTypes?: string[]; camera?: string }) => void }) {
  const storeLogs = useStore((s) => s.operationLogs)
  const items = (logs ?? storeLogs.map(l => ({
    id: l.id,
    timestamp: new Date(l.timestamp),
    user: l.user,
    action: l.action,
    violationTypes: Array.isArray(l.violationTypes) && l.violationTypes.length
      ? l.violationTypes
      : (l as any).violationType
        ? [(l as any).violationType]
        : [],
    trackId: l.trackId,
    plate: l.plate ?? '',
    camera: l.camera,
    details: l.details,
  })))
  // Hàm lấy icon và color cho action
  const getActionInfo = (action: string) => {
    switch (action) {
      case 'confirm':
        return { icon: <CheckCircleOutlined />, color: 'success', text: 'Xác nhận' }
      case 'skip':
        return { icon: <CloseCircleOutlined />, color: 'error', text: 'Bỏ qua' }
      default:
        return { icon: <ClockCircleOutlined />, color: 'default', text: 'Khác' }
    }
  }

  // Hàm format thời gian
  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(diff / (1000 * 60 * 60))
    
    if (minutes < 1) return 'Vừa xong'
    if (minutes < 60) return `${minutes} phút trước`
    if (hours < 24) return `${hours} giờ trước`
    return date.toLocaleDateString('vi-VN')
  }

  return (
    <Card 
      title={
        <Space>
          <ClockCircleOutlined />
          <span>Nhật ký thao tác</span>
        </Space>
      }
      className="operation-log-card"
      bodyStyle={{ padding: 12 }}
      style={{ height: '100%' }}
    >
      <div className="operation-log-list">
        {items.map(log => {
          const actionInfo = getActionInfo(log.action)
          return (
            <div
              key={log.id}
              className="log-entry"
              style={{ cursor: onSelect ? 'pointer' : 'default' }}
              onClick={() => onSelect?.({ trackId: log.trackId, plate: log.plate, violationTypes: log.violationTypes, camera: log.camera })}
            >
              <div className="log-header">
                <Space size="small">
                  <Tag color={actionInfo.color} icon={actionInfo.icon}>
                    {actionInfo.text}
                  </Tag>
                  <Space size={4} wrap>
                    {log.violationTypes?.length
                      ? log.violationTypes.map((label) => (
                        <Tag key={label} color={violationTypeToTagColor(label)} style={{ margin: 0 }}>
                          {label}
                        </Tag>
                      ))
                      : <Text strong style={{ fontSize: 12 }}>—</Text>}
                  </Space>
                </Space>
                <Text type="secondary" style={{ fontSize: 11 }}>
                  {formatTime(log.timestamp)}
                </Text>
              </div>
              
              <div className="log-details">
                <div className="log-info">
                  {log.user && (
                    <Text type="secondary" style={{ fontSize: 11 }}>
                      <UserOutlined style={{ marginRight: 4 }} />
                      {log.user}
                    </Text>
                  )}
                  <Text type="secondary" style={{ fontSize: 11 }}>
                    {log.camera}
                  </Text>
                </div>
                <Text strong style={{ fontSize: 12, color: 'var(--text)' }}>
                  {log.plate}
                </Text>
                {log.details && (
                  <Text type="secondary" style={{ fontSize: 11, fontStyle: 'italic' }}>
                    {log.details}
                  </Text>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
