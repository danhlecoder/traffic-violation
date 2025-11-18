import { Modal, Form, InputNumber, Switch, Button, Space } from 'antd'
import { useEffect } from 'react'

export interface CameraDetectionRules {
  speedLimit?: number
  minConfidence?: number
  enableRedLightCheck?: boolean
  enableHelmetCheck?: boolean
  enableSpeedCheck?: boolean
}

interface CameraDetectionRulesModalProps {
  open: boolean
  cameraId: string
  cameraName: string
  rules?: CameraDetectionRules
  onSave: (cameraId: string, rules: CameraDetectionRules) => Promise<void>
  onCancel: () => void
}

export default function CameraDetectionRulesModal({
  open,
  cameraId,
  cameraName,
  rules,
  onSave,
  onCancel,
}: CameraDetectionRulesModalProps) {
  const [form] = Form.useForm()

  useEffect(() => {
    if (open) {
      // Nếu có rules, dùng rules, nếu không dùng giá trị mặc định
      form.setFieldsValue({
        speedLimit: rules?.speedLimit ?? 60,
        minConfidence: rules?.minConfidence ?? 0.6,
        enableRedLightCheck: rules?.enableRedLightCheck ?? true,
        enableHelmetCheck: rules?.enableHelmetCheck ?? true,
        enableSpeedCheck: rules?.enableSpeedCheck ?? true,
      })
    }
  }, [open, rules, form])

  const handleSave = async () => {
    try {
      const values = await form.validateFields()
      await onSave(cameraId, {
        speedLimit: values.speedLimit,
        minConfidence: values.minConfidence,
        enableRedLightCheck: values.enableRedLightCheck,
        enableHelmetCheck: values.enableHelmetCheck,
        enableSpeedCheck: values.enableSpeedCheck,
      })
      form.resetFields()
    } catch (error) {
      console.error('Validation failed:', error)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    onCancel()
  }

  return (
    <Modal
      title={`Thiết lập luật phát hiện - ${cameraName}`}
      open={open}
      onCancel={handleCancel}
      footer={
        <Space>
          <Button onClick={handleCancel}>Hủy</Button>
          <Button type="primary" onClick={handleSave}>
            Lưu
          </Button>
        </Space>
      }
      width={600}
    >
      <Form form={form} layout="vertical">
        <Form.Item
          label="Ngưỡng tốc độ (km/h)"
          name="speedLimit"
          rules={[{ required: true, message: 'Vui lòng nhập ngưỡng tốc độ' }]}
        >
          <InputNumber min={0} max={200} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item
          label="Độ tin cậy tối thiểu"
          name="minConfidence"
          rules={[{ required: true, message: 'Vui lòng nhập độ tin cậy' }]}
        >
          <InputNumber step={0.01} min={0} max={1} style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item label="Phát hiện vượt đèn đỏ" name="enableRedLightCheck" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item label="Không đội mũ BH" name="enableHelmetCheck" valuePropName="checked">
          <Switch />
        </Form.Item>

        <Form.Item label="Quá tốc độ" name="enableSpeedCheck" valuePropName="checked">
          <Switch />
        </Form.Item>
      </Form>
    </Modal>
  )
}

