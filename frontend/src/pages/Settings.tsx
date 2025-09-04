import { useState } from 'react'
import { useStore } from '../store/useStore'
import { Card, Form, InputNumber, Switch, Input, Button, Table, Space, Modal, Divider, Typography, Row, Col } from 'antd'
import toast from 'react-hot-toast'

export default function Settings() {
  const settings = useStore((s) => s.settings)
  const update = useStore((s) => s.updateSettings)
  const [local, setLocal] = useState(settings)
  const smallPad = 12

  function save() {
    update(local)
    toast.success('Đã lưu cấu hình')
  }

  function addCamera() {
    const newId = `cam-${String(local.cameras.length + 1).padStart(2, '0')}`
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
      onOk: () => { setLocal({ ...local, cameras: local.cameras.filter((c) => c.id !== id) }); toast.success('Đã xóa camera') },
    })
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

      <Card title="Quản lý Camera" size="small" bodyStyle={{ padding: smallPad }} extra={<Space><Button size="small" onClick={addCamera}>Thêm</Button><Button size="small" type="primary" onClick={save}>Lưu</Button></Space>}>
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
