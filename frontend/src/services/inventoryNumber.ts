export function incrementInventoryNumber(value: string | null | undefined): string {
  const normalized = value?.trim() ?? ''
  if (!normalized) return '1'

  let digitStart = normalized.length
  while (digitStart > 0) {
    const character = normalized[digitStart - 1] ?? ''
    if (character < '0' || character > '9') break
    digitStart -= 1
  }

  if (digitStart === normalized.length) {
    return normalized.endsWith('-') ? `${normalized}1` : `${normalized}-1`
  }

  const prefix = normalized.slice(0, digitStart)
  const digits = normalized.slice(digitStart)
  const next = String(Number.parseInt(digits, 10) + 1).padStart(digits.length, '0')
  return `${prefix}${next}`
}
