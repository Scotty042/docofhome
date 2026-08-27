export async function copyText(text: string): Promise<void> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
      return
    }
  } catch {
    // In insecure contexts and restricted webviews the legacy fallback can
    // still work even though the Clipboard API is present.
  }

  const field = document.createElement('textarea')
  field.value = text
  field.setAttribute('readonly', '')
  field.style.position = 'fixed'
  field.style.opacity = '0'
  document.body.appendChild(field)
  field.focus()
  field.select()
  try {
    if (!document.execCommand('copy')) throw new Error('Copy command was rejected')
  } finally {
    field.remove()
  }
}
