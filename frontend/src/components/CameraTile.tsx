import { Badge, Typography, Tag } from 'antd'
import { useMemo } from 'react'

const { Text } = Typography

export default function CameraTile({ 
  name, 
  location, 
  rtsp, 
  height, 
  onDoubleClick, 
  focused,
  vehicleDensity = 0 // Mật độ phương tiện mặc định là 0
}: { 
  name: string; 
  location?: string; 
  rtsp?: string; 
  height?: number | string; 
  onDoubleClick?: () => void; 
  focused?: boolean;
  vehicleDensity?: number;
}) {
  const ready = useMemo(() => Boolean(rtsp), [rtsp])
  
  // Xác định màu badge dựa trên mật độ
  const getDensityColor = (density: number) => {
    if (density === 0) return 'default'
    if (density <= 5) return 'success'
    if (density <= 15) return 'warning'
    return 'error'
  }
  
  // Xác định text mô tả mật độ
  const getDensityText = (density: number) => {
    if (density === 0) return 'Vắng'
    if (density <= 5) return 'Thưa'
    if (density <= 15) return 'Đông'
    return 'Rất đông'
  }
  
  return (
    <div className={`camera-tile ${focused ? 'focused' : ''}`} onDoubleClick={onDoubleClick} title="Nhấp đúp để phóng to/thu nhỏ" style={{ cursor: focused ? 'zoom-out' : 'zoom-in' }}>
      <div className="camera-stream" style={height ? { height } : undefined}>
        <div className="camera-stream-inner">
          <div className="camera-stream-text">{ready ? 'Đang hiển thị stream' : 'Chưa cấu hình stream'}</div>
        </div>
      </div>
      
      {/* Hiển thị mật độ phương tiện trên camera */}
      <div className="camera-density-overlay">
        <Tag color={getDensityColor(vehicleDensity)} style={{ 
          margin: 0, 
          fontSize: '11px', 
          fontWeight: 600,
          border: 'none',
          borderRadius: '4px'
        }}>
          {vehicleDensity} xe
        </Tag>
        <div className="density-text" style={{ 
          fontSize: '10px', 
          color: 'rgba(255,255,255,0.8)', 
          marginTop: '2px',
          textAlign: 'center'
        }}>
          {getDensityText(vehicleDensity)}
        </div>
      </div>
      
      <div className="camera-footer">
        <div className="camera-name">
          <Text>{name}</Text>
          {location && <Text type="secondary" style={{ marginLeft: 8 }}>• {location}</Text>}
        </div>
        <div>
          <Badge status={ready ? 'success' : 'default'} text={ready ? 'Ready' : 'Idle'} />
        </div>
      </div>
    </div>
  )
}
