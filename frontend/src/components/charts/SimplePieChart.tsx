import React from 'react'
import { palette } from './utils'

export type PieDatum = { label: string; value: number; color?: string }

export default function SimplePieChart({ data, size = 200 }: { data: PieDatum[]; size?: number }) {
  const total = Math.max(1, data.reduce((s, d) => s + d.value, 0))
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - 10
  let acc = 0
  const strokes = data.map((d, i) => {
    const angle = (d.value / total) * 2 * Math.PI
    const x1 = cx + r * Math.cos(acc)
    const y1 = cy + r * Math.sin(acc)
    acc += angle
    const x2 = cx + r * Math.cos(acc)
    const y2 = cy + r * Math.sin(acc)
    const largeArc = angle > Math.PI ? 1 : 0
    const path = `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`
    return { path, color: d.color || palette(i) }
  })
  return (
    <div style={{ height: size }}>
      <svg width="100%" height="100%" viewBox={`0 0 ${size} ${size}`} preserveAspectRatio="xMidYMid meet">
        {strokes.map((s, i) => (
          <path key={i} d={s.path} fill={s.color} opacity={0.9} />
        ))}
        <circle cx={cx} cy={cy} r={r} fill="transparent" stroke="var(--border)" strokeWidth="1" />
      </svg>
    </div>
  )
}

