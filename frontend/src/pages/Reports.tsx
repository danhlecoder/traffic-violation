import { useMemo, useState } from 'react'
import { Card, Empty, Space, Typography, Statistic, Row, Col, Tag, Select, DatePicker } from 'antd'
import { useStore, VIOLATION_TYPES } from '../store/useStore'
import SimpleBarChart from '../components/charts/SimpleBarChart'
import SimplePieChart from '../components/charts/SimplePieChart'
import { palette } from '../components/charts/utils'
import { VIOLATION_STATUSES, STATUS_TAG_COLOR } from '../constants/violations'

export default function Reports() {
  const violations = useStore((s) => s.violations)
  const cameras = useStore((s) => s.settings.cameras)

  const [cameraId, setCameraId] = useState<string>('ALL')
  const [typeFilter, setTypeFilter] = useState<string>('ALL')
  const [range, setRange] = useState<any>(null) // Dayjs[] | null

  const filtered = useMemo(() => {
    return violations.filter(v => {
      if (!(cameraId === 'ALL' ? true : v.cameraId === cameraId)) return false
      if (!(typeFilter === 'ALL' ? true : v.type === typeFilter)) return false
      if (range && range[0] && range[1]) {
        const ts = new Date(v.time).getTime()
        const start = (range[0] as any)?.valueOf?.() ?? new Date(range[0]).getTime()
        const end = (range[1] as any)?.valueOf?.() ?? new Date(range[1]).getTime()
        if (ts < start || ts > end) return false
      }
      return true
    })
  }, [violations, cameraId, typeFilter, range])

  const total = filtered.length

  const groupedByType = useMemo(() => {
    const map: Record<string, number> = {}
    for (const v of filtered) map[v.type] = (map[v.type] || 0) + 1
    return Object.entries(map).sort((a, b) => b[1] - a[1])
  }, [filtered])

  const barData = useMemo(() => groupedByType.map(([label, value], i) => ({ label, value, color: palette(i) })), [groupedByType])
  const pieData = barData

  const statusColor = STATUS_TAG_COLOR

  const cameraOptions = [{ value: 'ALL', label: 'Tất cả camera' }, ...cameras.map(c => ({ value: c.id, label: `${c.name} — ${c.location}` }))]
  const cameraLabel = cameraOptions.find(o => o.value === cameraId)?.label || 'Tất cả camera'

  return (
    <Space direction="vertical" style={{ width: '100%' }} size={16}>
      <Row gutter={12}>
        <Col xs={24} md={12}>
          <Card title="Tổng quan">
            <Row gutter={12}>
              <Col span={12}><Statistic title="Tổng" value={total} /></Col>
              <Col span={12}><Statistic title="Vi phạm đã xác nhận" value={violations.filter(v=>v.status==='Đã xác nhận').length} /></Col>
            </Row>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="Bộ lọc">
            <Space wrap>
              <Select
                value={cameraId}
                onChange={(v) => setCameraId(v)}
                options={cameraOptions}
                style={{ minWidth: 220 }}
              />
              <Select
                value={typeFilter}
                onChange={(v) => setTypeFilter(v)}
                options={[{ value: 'ALL', label: 'Tất cả loại' }, ...VIOLATION_TYPES.map(t => ({ value: t, label: t }))]}
                style={{ minWidth: 160 }}
              />
              <DatePicker.RangePicker
                value={range}
                onChange={(v) => setRange(v)}
                showTime
                allowClear
              />
            </Space>
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col xs={24} md={14}>
          <Card title={`Biểu đồ cột theo loại (${cameraLabel.toLowerCase()})`}>
            {barData.length === 0 ? (
              <Empty description="Chưa có dữ liệu" />
            ) : (
              <>
                <SimpleBarChart data={barData} />
                <Space wrap size={8} style={{ marginTop: 8 }}>
                  {barData.map((d) => (
                    <Tag key={d.label} color={d.color} style={{ color: '#0f172a' }}>{d.label}: {d.value}</Tag>
                  ))}
                </Space>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} md={10}>
          <Card title={`Biểu đồ tròn theo loại (${cameraLabel.toLowerCase()})`}>
            {pieData.length === 0 ? (
              <Empty description="Chưa có dữ liệu" />
            ) : (
              <>
                <SimplePieChart data={pieData} />
                <Space wrap size={8} style={{ marginTop: 8 }}>
                  {pieData.map((d) => (
                    <Tag key={d.label} color={d.color} style={{ color: '#0f172a' }}>{d.label}: {d.value}</Tag>
                  ))}
                </Space>
              </>
            )}
          </Card>
        </Col>
      </Row>

      <Card title="Theo trạng thái (tất cả)">
        <Space size={12} wrap>
          {VIOLATION_STATUSES.map(s => (
            <Tag key={s} color={statusColor[s]}>{s}: {violations.filter(v=> v.status===s).length}</Tag>
          ))}
        </Space>
      </Card>
    </Space>
  )
}
