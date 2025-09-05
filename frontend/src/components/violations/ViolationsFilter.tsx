import { Space, Input, Select, DatePicker } from 'antd'
import { useStore, VIOLATION_TYPES } from '../../store/useStore'
import { VIOLATION_STATUSES } from '../../constants/violations'

export interface ViolationsFilterProps {
  q: string
  onQChange: (v: string) => void
  cameraId: string
  onCameraIdChange: (v: string) => void
  type: string
  onTypeChange: (v: string) => void
  status: string
  onStatusChange: (v: string) => void
  range: any
  onRangeChange: (v: any) => void
}

export default function ViolationsFilter({
  q,
  onQChange,
  cameraId,
  onCameraIdChange,
  type,
  onTypeChange,
  status,
  onStatusChange,
  range,
  onRangeChange,
}: ViolationsFilterProps) {
  const cameras = useStore((s) => s.settings.cameras)

  return (
    <Space style={{ marginBottom: 12 }} wrap>
      <Input
        placeholder="Tìm BSX, camera, địa điểm..."
        value={q}
        onChange={(e) => onQChange(e.target.value)}
        allowClear
        style={{ minWidth: 220 }}
      />
      <Select
        value={cameraId || undefined}
        onChange={onCameraIdChange}
        allowClear
        placeholder="Tất cả camera"
        style={{ minWidth: 220 }}
        options={cameras.map((c) => ({ value: c.id, label: `${c.name} — ${c.location}` }))}
      />
      <Select
        value={type || undefined}
        onChange={onTypeChange}
        allowClear
        placeholder="Tất cả loại"
        style={{ minWidth: 160 }}
        options={VIOLATION_TYPES.map((t) => ({ value: t, label: t }))}
      />
      <Select
        value={status || undefined}
        onChange={onStatusChange}
        allowClear
        placeholder="Tất cả trạng thái"
        style={{ minWidth: 160 }}
        options={VIOLATION_STATUSES.map((s) => ({ value: s, label: s }))}
      />
      <DatePicker.RangePicker value={range} onChange={onRangeChange} showTime allowClear />
    </Space>
  )
}

