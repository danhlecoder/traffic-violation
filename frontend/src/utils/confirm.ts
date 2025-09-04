import { Modal } from 'antd'

export function confirmAction(message: string): Promise<boolean> {
  return new Promise<boolean>((resolve) => {
    const modal = Modal.confirm({
      title: message,
      okText: 'Xác nhận',
      cancelText: 'Hủy',
      centered: true,
      maskClosable: true,
      onOk: () => { modal.destroy(); resolve(true) },
      onCancel: () => { modal.destroy(); resolve(false) },
    })
  })
}

