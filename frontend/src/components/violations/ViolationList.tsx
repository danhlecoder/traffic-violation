import { Card, List, Tag, Typography } from 'antd'
import type { Violation } from '../../store/useStore'
import { isPlaceholder } from '../../utils/media'
import { STATUS_TAG_COLOR, getViolationTypes, violationTypeToTagColor } from '../../constants/violations'

const { Text } = Typography

export default function ViolationList({ items, onClick, height }: { items: Violation[]; onClick: (v: Violation) => void; height?: number | string }) {
  return (
    <Card className="right-sticky" style={height ? { height } : undefined} bodyStyle={{ height: '100%', padding: 8 }}>
      <div className="scroll-body" style={{ height: '100%', overflow: 'auto' }}>
        <List
          dataSource={items}
          renderItem={(v) => {
            const types = getViolationTypes(v)
            const thumbSrc = isPlaceholder(v.images?.overview) ? undefined : v.images.overview
            const hasImg = Boolean(thumbSrc)
            return (
              <div onClick={() => onClick(v)} className="vl-item-new" style={{ cursor: 'pointer' }}>
                {/* Thumbnail nhỏ gọn hơn */}
                <div className={`vl-thumb-new ${hasImg ? 'has-img' : ''}`} style={hasImg ? { backgroundImage: `url(${thumbSrc})` } : undefined} />

                {/* Nội dung chính - compact layout */}
                <div className="vl-main">
                  <div className="vl-header">
                    <Tag color={violationTypeToTagColor(types[0] || v.type)}>{types[0] || v.type}</Tag>
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
                  <Tag color={STATUS_TAG_COLOR[v.status]}>
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
