import React from 'react'
import { palette } from './utils'

export type BarDatum = { label: string; value: number; color?: string }

export default function SimpleBarChart({ data, height = 200 }: { data: BarDatum[]; height?: number }) {
  const max = Math.max(1, ...data.map(d => d.value))
  const barWidth = Math.max(12, Math.min(26, Math.floor(220 / Math.max(1, data.length))))
  const gap = 12
  const chartWidth = data.length * (barWidth + gap) + gap
  return (
    <div style={{ height }}>
      <svg width="100%" height="100%" viewBox={`0 0 ${chartWidth} ${height}`} preserveAspectRatio="xMidYMid meet">
        {data.map((d, i) => {
          const h = Math.round(((d.value / max) * (height - 42)))
          const x = gap + i * (barWidth + gap)
          const y = height - 24 - h
          return (
            <g key={d.label}>
              <rect x={x} y={y} width={barWidth} height={h} rx={4} fill={d.color || palette(i)} />
              <text x={x + barWidth / 2} y={y - 4} textAnchor="middle" fontSize="11" fill="var(--text)" fontWeight={600}>{d.value}</text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

