import { Link } from 'react-router-dom'
import { Result, Button } from 'antd'

export default function NotFound() {
  return (
    <Result
      status="404"
      title="Không tìm thấy"
      subTitle="Trang bạn truy cập không tồn tại."
      extra={<Button type="primary"><Link to="/giam-sat">Về giám sát</Link></Button>}
    />
  )
}
