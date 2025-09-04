import { Card, Select, Space, Button } from 'antd'
import { useStore } from '../store/useStore'

export default function VideoPanel() {
  const cameras = useStore((s) => s.settings.cameras)
  return (
    <Card title="Luồng camera" extra={<Select style={{ minWidth: 220 }} defaultValue={cameras[0]?.id} options={cameras.map(c => ({ value: c.id, label: `${c.name} — ${c.location}` }))} />}> 
      <img src="/placeholders/panorama.svg" alt="camera" style={{ width: '100%', borderRadius: 8 }} />
      <div style={{ marginTop: 12 }}>
        <Space>
          <Button type="primary">Tạm dừng</Button>
          <Button>Chụp ảnh</Button>
          <Button>Video kiểm thử</Button>
        </Space>
      </div>
    </Card>
  )
}

