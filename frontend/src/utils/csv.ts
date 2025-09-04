export function toCsv(rows: (string | number | null | undefined)[][], header?: (string | number)[]) {
  const escape = (x: any) => `"${String(x ?? '').replace(/"/g, '""')}"`
  const lines = header ? [header, ...rows] : rows
  return lines.map(r => r.map(escape).join(',')).join('\n')
}

export function downloadCsv(filename: string, rows: (string | number | null | undefined)[][], header?: (string | number)[]) {
  const csv = toCsv(rows, header)
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

