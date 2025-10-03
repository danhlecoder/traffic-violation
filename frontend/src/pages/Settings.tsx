import { useState } from 'react'
import { useStore } from '../store/useStore'
import { streams } from '../services/api'
import { Card, Form, InputNumber, Switch, Input, Button, Table, Space, Modal, Divider, Typography, Row, Col, Upload } from 'antd'
import { UploadOutlined, DownloadOutlined } from '@ant-design/icons'
import toast from 'react-hot-toast'

export default function Settings() {
  const settings = useStore((s) => s.settings)
  const update = useStore((s) => s.updateSettings)
  const [local, setLocal] = useState(settings)
  const smallPad = 12

  function save() {
    // Kiểm tra trùng ID trước khi lưu
    const ids = local.cameras.map((c) => c.id)
    const dup = ids.find((id, idx) => ids.indexOf(id) !== idx)
    if (dup) {
      toast.error(`Trùng ID camera: ${dup}. Vui lòng đổi ID trước khi lưu.`)
      return
    }
    update(local)
    // Đồng bộ danh sách camera lên backend để lưu cùng regions
    Promise.all(local.cameras.map((c) => streams.upsertCamera({ id: c.id, name: c.name, rtsp: c.rtsp, location: c.location, regions: (useStore.getState().settings.cameraRegions as any)[c.id] }))).then(() => {
      toast.success('Đã lưu cấu hình')
    }).catch(() => toast.error('Lưu server thất bại (offline?)'))
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
          await streams.deleteCamera(id)
        } catch (e) {
          toast.error('Xóa trên server thất bại')
          return
        }

        // Cập nhật store (persist vào localStorage) và local state đồng bộ
        const nextCams = local.cameras.filter((c) => c.id !== id)
        const nextRegions = { ...(useStore.getState().settings.cameraRegions || {}) } as any
        if (nextRegions[id]) delete nextRegions[id]
        update({ cameras: nextCams, cameraRegions: nextRegions })
        setLocal({ ...local, cameras: nextCams, cameraRegions: nextRegions })
        toast.success('Đã xóa camera')
      },
    })
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
    <Space direction="vertical" size={12} style={{ width: '100%' }}>
      <Row gutter={12}>
        <Col xs={24} md={12}>
          <Card title="Luật phát hiện" size="small" bodyStyle={{ padding: smallPad }}>
            <Form layout="vertical">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <Form.Item label="Ngưỡng tốc độ (km/h)" style={{ marginBottom: 10 }}>
                  <InputNumber min={0} value={local.speedLimit} onChange={(v) => setLocal({ ...local, speedLimit: Number(v || 0) })} style={{ width: '100%' }} />
                </Form.Item>
                <Form.Item label="Độ tin cậy tối thiểu" style={{ marginBottom: 10 }}>
                  <InputNumber step={0.01} min={0} max={1} value={local.minConfidence} onChange={(v) => setLocal({ ...local, minConfidence: Number(v || 0) })} style={{ width: '100%' }} />
                </Form.Item>
              </div>
              <Divider style={{ margin: '8px 0' }} />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Typography.Text>Phát hiện vượt đèn đỏ</Typography.Text>
                  <Switch checked={local.enableRedLightCheck} onChange={(v) => setLocal({ ...local, enableRedLightCheck: v })} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Typography.Text>Không đội mũ BH</Typography.Text>
                  <Switch checked={local.enableHelmetCheck} onChange={(v) => setLocal({ ...local, enableHelmetCheck: v })} />
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Typography.Text>Quá tốc độ</Typography.Text>
                  <Switch checked={local.enableSpeedCheck} onChange={(v) => setLocal({ ...local, enableSpeedCheck: v })} />
                </div>
              </div>
              <div style={{ textAlign: 'right', marginTop: 8 }}>
                <Button type="primary" size="small" onClick={save}>Lưu</Button>
              </div>
            </Form>
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="Tích hợp Zalo" size="small" bodyStyle={{ padding: smallPad }}>
            <Form layout="vertical">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <Form.Item label="ZALO Access Token" style={{ marginBottom: 10 }}>
                  <Input value={local.zaloToken} onChange={(e) => setLocal({ ...local, zaloToken: e.target.value })} placeholder="Token..." />
                </Form.Item>
                <Form.Item label="Đích gửi (User/Group ID)" style={{ marginBottom: 10 }}>
                  <Input value={local.zaloTargetId} onChange={(e) => setLocal({ ...local, zaloTargetId: e.target.value })} placeholder="ID..." />
                </Form.Item>
              </div>
              <div style={{ textAlign: 'right' }}>
                <Button type="primary" size="small" onClick={save}>Lưu</Button>
              </div>
            </Form>
          </Card>
        </Col>
      </Row>

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
            { title: 'Hành động', dataIndex: 'id', width: 120, render: (id: string) => <Button size="small" danger onClick={() => removeCamera(id)}>Xóa</Button> },
          ]}
        />
      </Card>
    </Space>
  )
}
