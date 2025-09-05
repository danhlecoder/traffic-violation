import { useMemo, useState } from 'react'
import { useStore, VIOLATION_TYPES, Violation } from '../store/useStore'
import { Table, Tag, Button } from 'antd'
import ViolationDetailModal from '../components/ViolationDetailModal'
import { confirmViolation, sendZalo, skipViolation } from '../services/api'
import toast from 'react-hot-toast'
import { confirmAction } from '../utils/confirm'
import { downloadCsv } from '../utils/csv'
import ViolationsFilter from '../components/violations/ViolationsFilter'

export default function Violations() {
  const list = useStore((s) => s.violations)
  const updateViolation = useStore((s) => s.updateViolation)
  const addOperationLog = useStore((s) => s.addOperationLog)
  const { zaloToken, zaloTargetId } = useStore((s) => s.settings)
  const [q, setQ] = useState('')
  const [type, setType] = useState<string>('')
  const [cameraId, setCameraId] = useState<string>('')
  const [status, setStatus] = useState<string>('')
  const [range, setRange] = useState<any>(null)
  const [selected, setSelected] = useState<Violation | null>(null)

  const filtered = useMemo(() => {
    return list.filter((v) => {
      const okType = !type || v.type === type
      const okCam = !cameraId || v.cameraId === cameraId
      const okStatus = !status || v.status === status
      const okQ = !q || `${v.plate} ${v.cameraName} ${v.location}`.toLowerCase().includes(q.toLowerCase())
      let okTime = true
      if (range && range[0] && range[1]) {
        const ts = new Date(v.time).getTime()
        const start = (range[0] as any)?.valueOf?.() ?? new Date(range[0]).getTime()
        const end = (range[1] as any)?.valueOf?.() ?? new Date(range[1]).getTime()
        okTime = ts >= start && ts <= end
      }
      return okType && okCam && okStatus && okQ && okTime
    })
  }, [list, q, type, cameraId, status, range])

  const statusColor: Record<string, string> = {
    'Mới': 'default',
    'Đã xác nhận': 'processing',
    'Đã bỏ qua': 'error',
  }

  function onDownloadCsv() {
    const header = ['Thời gian','Loại','BSX','Camera','Vị trí','Trạng thái']
    const rows = filtered.map(v => [new Date(v.time).toLocaleString('vi-VN'), v.type, v.plate ?? '', v.cameraName, v.location, v.status])
    downloadCsv('violations.csv', rows, header)
  }

  async function onConfirm(v: Violation): Promise<boolean> {
    const ok = await confirmAction('Xác nhận vi phạm này?')
    if (!ok) return false
    await confirmViolation(v.id)
    updateViolation(v.id, { status: 'Đã xác nhận' })
    addOperationLog({
      id: `${v.id}-confirm-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user: '',
      action: 'confirm',
      violationType: v.type,
      plate: v.plate,
      camera: v.cameraName,
      details: 'Xác nhận vi phạm'
    })
    if (zaloToken && zaloTargetId) {
      await sendZalo(v, zaloToken, zaloTargetId)
    }
    toast.success('Đã xác nhận vi phạm')
    return true
  }

  async function onSkip(v: Violation): Promise<boolean> {
    const ok = await confirmAction('Bỏ qua vi phạm này?')
    if (!ok) return false
    await skipViolation(v.id)
    updateViolation(v.id, { status: 'Đã bỏ qua' })
    addOperationLog({
      id: `${v.id}-skip-${Date.now()}`,
      timestamp: new Date().toISOString(),
      user: '',
      action: 'skip',
      violationType: v.type,
      plate: v.plate,
      camera: v.cameraName,
      details: 'Bỏ qua vi phạm'
    })
    toast('Đã bỏ qua', { icon: '🗑️' })
    return true
  }

  return (
    <>
      <div className="page-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span>Danh sách</span>
        <Button onClick={onDownloadCsv}>Tải CSV</Button>
      </div>
      <ViolationsFilter
        q={q}
        onQChange={setQ}
        cameraId={cameraId}
        onCameraIdChange={setCameraId}
        type={type}
        onTypeChange={setType}
        status={status}
        onStatusChange={setStatus}
        range={range}
        onRangeChange={setRange}
      />
      <Table
        rowKey="id"
        dataSource={filtered}
        pagination={{ pageSize: 10 }}
        columns={[
          { title: 'Thời gian', dataIndex: 'time', render: (t: string) => new Date(t).toLocaleString('vi-VN') },
          { title: 'Loại', dataIndex: 'type' },
          { title: 'BSX', dataIndex: 'plate', render: (x: string) => x ?? '—' },
          { title: 'Camera', dataIndex: 'cameraName' },
          { title: 'Vị trí', dataIndex: 'location' },
          { title: 'Trạng thái', dataIndex: 'status', render: (s: string) => <Tag color={statusColor[s]}>{s}</Tag> },
          { title: 'Ảnh', dataIndex: ['images', 'vehicle'], render: (_: string, v: Violation) => <a onClick={() => setSelected(v)}>Xem</a> },
        ]}
      />
      <ViolationDetailModal
        open={!!selected}
        onClose={() => setSelected(null)}
        data={selected ?? undefined}
        onConfirm={async () => selected ? await onConfirm(selected) : false}
        onSkip={async () => selected ? await onSkip(selected) : false}
      />
    </>
  )
}
