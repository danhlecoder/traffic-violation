import { Card, Space, Button, Tag, Typography } from 'antd'
import type { Violation } from '../../store/useStore'
import { STATUS_TAG_COLOR } from '../../constants/violations'

const { Text } = Typography

export default function ViolationCard({ v, onDetail, onConfirm, onSkip, onSendZalo }: {
  v: Violation
  onDetail: () => void
  onConfirm: () => void
  onSkip: () => void
  onSendZalo: () => void
}) {
  return (
    <Card
      size="small"
      cover={<img alt="vehicle" src={v.images.vehicle} style={{ height: 160, objectFit: 'cover' }} />}
      actions={[
        <Button type="link" onClick={onDetail} key="d">Chi tiết</Button>,
        <Button type="link" onClick={onConfirm} key="c">Xác nhận</Button>,
        <Button type="link" danger onClick={onSkip} key="s">Bỏ qua</Button>,
        <Button type="link" onClick={onSendZalo} key="z">Gửi Zalo</Button>,
      ]}
    >
      <Space direction="vertical" style={{ width: '100%' }} size={6}>
        <Space style={{ justifyContent: 'space-between', width: '100%' }}>
          <Text strong>{v.type}</Text>
          <Tag color={STATUS_TAG_COLOR[v.status]}>{v.status}</Tag>
        </Space>
        <Text type="secondary">BSX: {v.plate ?? '—'} · {new Date(v.time).toLocaleString('vi-VN')}</Text>
        <Text type="secondary">Camera: {v.cameraName} — {v.location}</Text>
        {v.speed && <Text type="secondary">Tốc độ: {v.speed} km/h</Text>}
      </Space>
    </Card>
  )
}
