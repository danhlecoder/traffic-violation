import { useState } from 'react'
import { useStore } from '../store/useStore'
import { upsertCamera, deleteCamera, updateCameraDetectionRules } from '../services/camera.service'
import { Card, Form, Input, Button, Table, Space, Modal, Row, Col, Upload } from 'antd'
import { UploadOutlined, DownloadOutlined, SettingOutlined } from '@ant-design/icons'
import toast from 'react-hot-toast'
import CameraDetectionRulesModal, { type CameraDetectionRules } from '../components/CameraDetectionRulesModal'

export default function Settings() {
  const settings = useStore((s) => s.settings)
  const update = useStore((s) => s.updateSettings)
  const [local, setLocal] = useState(settings)
  const [detectionRulesModal, setDetectionRulesModal] = useState<{
    open: boolean
    cameraId: string
    cameraName: string
    rules?: CameraDetectionRules
  }>({ open: false, cameraId: '', cameraName: '' })
  const smallPad = 12

  // State để lưu detection rules tạm thời cho camera (kể cả camera chưa lưu vào DB)
  const [cameraDetectionRules, setCameraDetectionRules] = useState<Record<string, CameraDetectionRules>>({})

  // Lấy detection rules từ camera trong DB hoặc từ state tạm thời
  const getCameraDetectionRules = async (cameraId: string): Promise<CameraDetectionRules | undefined> => {
    // Nếu có trong state tạm thời, dùng luôn
    if (cameraDetectionRules[cameraId]) {
      return cameraDetectionRules[cameraId]
    }

    // Nếu không, thử lấy từ DB
    try {
      const { getCamera } = await import('../services/camera.service')
      const camera = await getCamera(cameraId)
      return camera.detection_rules
    } catch (e) {
      // Camera chưa có trong DB, trả về undefined để dùng giá trị mặc định
      return undefined
    }
  }

  async function save() {
    // Kiểm tra trùng ID trước khi lưu
    const ids = local.cameras.map((c) => c.id)
    const dup = ids.find((id, idx) => ids.indexOf(id) !== idx)
    if (dup) {
      toast.error(`Trùng ID camera: ${dup}. Vui lòng đổi ID trước khi lưu.`)
      return
    }
    update(local)

    // Đồng bộ danh sách camera lên backend để lưu cùng regions và detection_rules
    try {
      await Promise.all(local.cameras.map(async (c) => {
        const cameraData: any = {
          id: c.id,
          name: c.name,
          rtsp: c.rtsp,
          location: c.location,
          regions: (useStore.getState().settings.cameraRegions as any)[c.id]
        }

        // Nếu có detection rules trong state tạm thời, thêm vào
        if (cameraDetectionRules[c.id]) {
          cameraData.detection_rules = cameraDetectionRules[c.id]
        }

        await upsertCamera(cameraData)
      }))

      toast.success('Đã lưu cấu hình')
    } catch (e) {
      console.error('Lỗi lưu camera:', e)
      toast.error('Lưu server thất bại (offline?)')
    }
  }

  function addCamera() {
    // Sinh ID tiếp theo không trùng: cam-01, cam-02, ... (lấy số nhỏ nhất chưa dùng)
    const used = new Set<number>()
    for (const c of local.cameras) {
      const m = /^cam-(\d+)$/.exec(c.id || '')
      if (m) {
        const n = parseInt(m[1], 10)
        if (!Number.isNaN(n)) used.add(n)
      }
    }
    let next = 1
    while (used.has(next)) next++
    const newId = `cam-${String(next).padStart(2, '0')}`
    setLocal({ ...local, cameras: [...local.cameras, { id: newId, name: 'Camera mới', rtsp: '', location: '' }] })
    toast.success('Đã thêm camera')
  }

  function removeCamera(id: string) {
    Modal.confirm({
      title: 'Xóa camera?',
      content: 'Thao tác này sẽ loại bỏ camera khỏi cấu hình.',
      okText: 'Xóa',
      okButtonProps: { danger: true },
      cancelText: 'Hủy',
      onOk: async () => {
        try {
          // Xóa dưới DB ngay lập tức
          await deleteCamera(id)
        } catch (e) {
          toast.error('Xóa trên server thất bại')
          return
        }

        // Cập nhật store (persist vào localStorage) và local state đồng bộ
        const nextCams = local.cameras.filter((c) => c.id !== id)
        const nextRegions = { ...(useStore.getState().settings.cameraRegions || {}) } as any
        if (nextRegions[id]) delete nextRegions[id]

        // Xóa detection rules tạm thời
        const nextRules = { ...cameraDetectionRules }
        if (nextRules[id]) delete nextRules[id]
        setCameraDetectionRules(nextRules)

        update({ cameras: nextCams, cameraRegions: nextRegions })
        setLocal({ ...local, cameras: nextCams, cameraRegions: nextRegions })
        toast.success('Đã xóa camera')
      },
    })
  }

  // Mở modal thiết lập detection rules
  async function openDetectionRulesModal(cameraId: string, cameraName: string) {
    // Lấy rules từ state tạm thời hoặc từ DB
    const rules = await getCameraDetectionRules(cameraId)
    setDetectionRulesModal({
      open: true,
      cameraId,
      cameraName,
      rules,
    })
  }

  // Lưu detection rules cho camera (có thể là camera chưa lưu vào DB)
  async function saveDetectionRules(cameraId: string, rules: CameraDetectionRules) {
    try {
      // Lưu vào state tạm thời trước (để có thể lưu cùng camera sau này)
      setCameraDetectionRules(prev => ({
        ...prev,
        [cameraId]: rules
      }))

      // Nếu camera đã có trong DB, lưu ngay
      try {
        // Kiểm tra camera có trong DB không
        const { getCamera } = await import('../services/camera.service')
        await getCamera(cameraId)

        // Camera đã có trong DB, lưu detection rules ngay
        await updateCameraDetectionRules(cameraId, rules)
        toast.success('Đã lưu luật phát hiện cho camera')
      } catch (e: any) {
        // Camera chưa có trong DB (404), chỉ lưu vào state tạm thời
        // Sẽ lưu cùng camera khi click "Lưu" trong Settings
        toast.success('Đã lưu luật phát hiện (sẽ áp dụng khi lưu camera)')
      }

      setDetectionRulesModal({ open: false, cameraId: '', cameraName: '' })
    } catch (e) {
      console.error('Lỗi lưu detection rules:', e)
      toast.error('Lưu luật phát hiện thất bại')
    }
  }

  // Xuất cấu hình vùng vẽ camera (cameraRegions) ra JSON để backup/chia sẻ
  function exportRegions() {
    const data = {
      cameraRegions: useStore.getState().settings.cameraRegions,
      exportedAt: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'camera-regions.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  // Nhập cấu hình vùng vẽ từ file JSON và ghi vào settings
  async function importRegions(file: File) {
    try {
      const text = await file.text()
      const parsed = JSON.parse(text)
      if (!parsed || typeof parsed !== 'object' || !parsed.cameraRegions) {
        toast.error('Tệp không hợp lệ')
        return
      }
      update({ cameraRegions: parsed.cameraRegions })
      setLocal({ ...local, cameraRegions: parsed.cameraRegions })
      toast.success('Đã nhập vùng vẽ từ file')
    } catch (e) {
      toast.error('Không thể đọc tệp JSON')
    }
  }

  return (
    <>
      <Space direction="vertical" size={12} style={{ width: '100%' }}>
        <Card
          title="Quản lý Camera"
          size="small"
          bodyStyle={{ padding: smallPad }}
          extra={
            <Space>
              <Button size="small" icon={<DownloadOutlined />} onClick={exportRegions}>Xuất vùng</Button>
              <Upload showUploadList={false} accept="application/json" beforeUpload={() => false} onChange={(e) => { const f = e.file as any; if (f?.originFileObj) importRegions(f.originFileObj) }}>
                <Button size="small" icon={<UploadOutlined />}>Nhập vùng</Button>
              </Upload>
              <Button size="small" onClick={addCamera}>Thêm</Button>
              <Button size="small" type="primary" onClick={save}>Lưu</Button>
            </Space>
          }
        >
          <Table
            size="small"
            bordered
            rowKey="id"
            pagination={false}
            dataSource={local.cameras}
            locale={{ emptyText: 'Trống' }}
            columns={[
              { title: 'ID', dataIndex: 'id', width: 120 },
              { title: 'Tên', dataIndex: 'name', render: (_: string, r, i) => <Input size="small" value={r.name} onChange={(e) => { const arr = [...local.cameras]; arr[i] = { ...arr[i], name: e.target.value }; setLocal({ ...local, cameras: arr }) }} /> },
              { title: 'RTSP', dataIndex: 'rtsp', render: (_: string, r, i) => <Input size="small" value={r.rtsp} onChange={(e) => { const arr = [...local.cameras]; arr[i] = { ...arr[i], rtsp: e.target.value }; setLocal({ ...local, cameras: arr }) }} /> },
              { title: 'Vị trí', dataIndex: 'location', render: (_: string, r, i) => <Input size="small" value={r.location} onChange={(e) => { const arr = [...local.cameras]; arr[i] = { ...arr[i], location: e.target.value }; setLocal({ ...local, cameras: arr }) }} /> },
              {
                title: 'Hành động',
                dataIndex: 'id',
                width: 180,
                render: (id: string, record: any) => (
                  <Space>
                    <Button
                      size="small"
                      icon={<SettingOutlined />}
                      onClick={() => openDetectionRulesModal(id, record.name)}
                    >
                      Thiết lập
                    </Button>
                    <Button size="small" danger onClick={() => removeCamera(id)}>
                      Xóa
                    </Button>
                  </Space>
                ),
              },
            ]}
          />
        </Card>
      </Space>

      <CameraDetectionRulesModal
        open={detectionRulesModal.open}
        cameraId={detectionRulesModal.cameraId}
        cameraName={detectionRulesModal.cameraName}
        rules={detectionRulesModal.rules}
        onSave={saveDetectionRules}
        onCancel={() => setDetectionRulesModal({ open: false, cameraId: '', cameraName: '' })}
      />
    </>
  )
}
