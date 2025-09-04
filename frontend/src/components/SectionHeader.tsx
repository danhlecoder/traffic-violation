import { ReactNode } from 'react'

export default function SectionHeader({ title, extra }: { title?: ReactNode; extra?: ReactNode }) {
  return (
    <div className="section-header">
      {title ? <div className="section-title">{title}</div> : <div />}
      <div className="section-extra">{extra}</div>
    </div>
  )
}
