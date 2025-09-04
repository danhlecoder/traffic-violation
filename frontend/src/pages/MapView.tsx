import { Card } from 'antd'

export default function MapView() {
  return (
    <Card title="Bản đồ camera">
      <div className="map-placeholder">Bản đồ sẽ hiển thị tại đây (tích hợp Mapbox/Leaflet ở bước sau)</div>
    </Card>
  )
}
