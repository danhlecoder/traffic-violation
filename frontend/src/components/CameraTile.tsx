import { Badge, Typography, Tag, Button, Tooltip } from 'antd'
import { useMemo, useState, useCallback, useEffect } from 'react'
import { EditOutlined } from '@ant-design/icons'
import { buildStreamUrl, fetchSnapshotBlob } from '../services/streams'
import RegionEditorModal from './RegionEditorModal'
import RegionOverlay from './RegionOverlay'
import { useStore } from '../store/useStore'
import { useElementScaler } from '../hooks/useElementScaler'

const { Text } = Typography

export default function CameraTile({
  cameraId,
  name,
  location,
  rtsp,
  height,
  onDoubleClick,
  focused,
  vehicleDensity = 0 // Mật độ phương tiện mặc định là 0
}: {
  cameraId: string;
  name: string;
  location?: string;
  rtsp?: string;
  height?: number | string;
  onDoubleClick?: () => void;
  focused?: boolean;
  vehicleDensity?: number;
}) {
  const ready = useMemo(() => Boolean(rtsp), [rtsp])
  const { ref: containerRef, toPixel } = useElementScaler<HTMLDivElement>()
  const [editorOpen, setEditorOpen] = useState(false)
  const [snapshot, setSnapshot] = useState<string | undefined>(undefined)
  const regions = useStore((s) => s.settings.cameraRegions)
  const cameraRegion = regions[cameraId] || {}

  const streamSrc = useMemo(() => (rtsp ? buildStreamUrl(rtsp) : undefined), [rtsp])

  // Capture a snapshot via backend endpoint; fallback to canvas if needed
  const takeSnapshot = useCallback(async () => {
    if (!rtsp) return
    // Mở modal ngay lập tức, ảnh snapshot sẽ tải bất đồng bộ
    setEditorOpen(true)
    try {
      const blob = await fetchSnapshotBlob(rtsp)
      const objectUrl = URL.createObjectURL(blob)
      setSnapshot(objectUrl)
      return
    } catch (e) {
      // Fallback to canvas from the <img> element
      const el = containerRef.current
      const img = el?.querySelector('img') as HTMLImageElement | null
      if (img) {
        try {
          const canvas = document.createElement('canvas')
          const w = img.naturalWidth || img.width
          const h = img.naturalHeight || img.height
          canvas.width = w
          canvas.height = h
          const ctx = canvas.getContext('2d')
          if (!ctx) throw new Error('No canvas context')
          ctx.drawImage(img, 0, 0, w, h)
          const data = canvas.toDataURL('image/jpeg', 0.92)
          setSnapshot(data)
        } catch {
          setSnapshot(undefined)
        }
      } else {
        setSnapshot(undefined)
      }
    }
  }, [rtsp])

  // Revoke blob URL when modal closes or component unmounts
  useEffect(() => {
    return () => {
      if (snapshot && snapshot.startsWith('blob:')) {
        try { URL.revokeObjectURL(snapshot) } catch {}
      }
    }
  }, [snapshot])

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
    <>
    <div className={`camera-tile ${focused ? 'focused' : ''}`} onDoubleClick={onDoubleClick} title="Nhấp đúp để phóng to/thu nhỏ" style={{ cursor: focused ? 'zoom-out' : 'zoom-in' }}>
      <div className="camera-stream" style={height ? { height } : undefined} ref={containerRef}>
        {ready && streamSrc ? (
          <img
            crossOrigin="anonymous"
            src={streamSrc}
            alt={name}
            style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
          />
        ) : (
          <div className="camera-stream-inner">
            <div className="camera-stream-text">Chưa cấu hình stream</div>
          </div>
        )}

        {/* Hiển thị overlay vùng đã lưu (read-only) */}
        <RegionOverlay region={cameraRegion} toPixel={toPixel} readOnly />

        {ready && (
          <div className="edit-btn-overlay">
            <Tooltip title="Thiết lập vùng trên ảnh chụp">
              <Button size="small" icon={<EditOutlined />} onClick={takeSnapshot}>Bút</Button>
            </Tooltip>
          </div>
        )}
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
    <RegionEditorModal open={editorOpen} cameraId={cameraId} imageSrc={snapshot} onClose={() => setEditorOpen(false)} />
    </>
  )
}
