export function isPlaceholder(u?: string) {
  if (!u) return true
  return u.includes('/placeholders/') || !u.trim()
}

