import { Card, List, Tag, Typography } from 'antd'
import type { Violation } from '../store/useStore'

const { Text } = Typography

function kindMeta(k: string) {
  if (k.includes('đèn đỏ')) return { tag: 'red', cls: 'is-red' }
  if (k.includes('tốc độ')) return { tag: 'cyan', cls: 'is-cyan' }
  return { tag: 'gold', cls: 'is-gold' }
}

function isPlaceholder(u?: string) {
  return !u || !u.trim() || u.includes('/placeholders/')
}

function statusToColor(s: string): 'default' | 'processing' | 'success' | 'error' | 'warning' {
  if (s === 'Đã xác nhận') return 'processing'
  if (s === 'Đã bỏ qua') return 'default'
  return 'warning'
}

function getTypes(v: any): string[] {
  if (Array.isArray(v?.types) && v.types.length) return v.types as string[]
  return [v.type]
}

export default function ViolationList({ items, onClick, height }: { items: Violation[]; onClick: (v: Violation) => void; height?: number | string }) {
  return (
    <Card className="right-sticky" style={height ? { height } : undefined} bodyStyle={{ height: '100%', padding: 8 }}>
      <div className="scroll-body" style={{ height: '100%', overflow: 'auto' }}>
        <List
          dataSource={items}
          renderItem={(v) => {
            const types = getTypes(v)
            const km = kindMeta(types[0] || v.type)
            const thumbSrc = isPlaceholder(v.images?.overview) ? undefined : v.images.overview
            const hasImg = Boolean(thumbSrc)
            return (
              <div onClick={() => onClick(v)} className="vl-item-new" style={{ cursor: 'pointer' }}>
                {/* Thumbnail nhỏ gọn hơn */}
                <div className={`vl-thumb-new ${hasImg ? 'has-img' : ''}`} style={hasImg ? { backgroundImage: `url(${thumbSrc})` } : undefined} />
                
                {/* Nội dung chính - compact layout */}
                <div className="vl-main">
                  <div className="vl-header">
                    <Tag color={kindMeta(types[0] || v.type).tag}>{types[0] || v.type}</Tag>
                    <Text strong style={{ fontSize: 13 }}>{v.cameraName}</Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>• {v.location}</Text>
                  </div>
                  
                  <div className="vl-details">
                    <div className="vl-time">{new Date(v.time).toLocaleString('vi-VN', { 
                      hour: '2-digit', 
                      minute: '2-digit', 
                      day: '2-digit', 
                      month: '2-digit' 
                    })}</div>
                    <div className="vl-plate">{v.plate ?? 'Chưa nhận diện'}</div>
                    {v.vehicleType && <div className="vl-vehicle">{v.vehicleType}</div>}
                    {typeof v.speed === 'number' && <div className="vl-speed">{v.speed} km/h</div>}
                  </div>
                </div>
                
                {/* Status ở góc phải */}
                <div className="vl-status-new">
                  <Tag color={statusToColor(v.status)}>
                    {v.status === 'Mới' ? 'Chờ duyệt' : v.status}
                  </Tag>
                </div>
              </div>
            )
          }}
        />
      </div>
    </Card>
  )
}
