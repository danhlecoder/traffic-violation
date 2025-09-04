import { useEffect, useState } from 'react'

function fmt(d: Date) {
  const p = (n: number) => String(n).padStart(2, '0')
  const hh = p(d.getHours())
  const mm = p(d.getMinutes())
  const ss = p(d.getSeconds())
  const dd = p(d.getDate())
  const mo = p(d.getMonth() + 1)
  const yy = d.getFullYear()
  return `${hh}:${mm}:${ss} ${dd}/${mo}/${yy}`
}

export default function Clock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return <span className="header-clock">{fmt(now)}</span>
}

