export function validateIntegrationUrl(
  value: string | null,
  required: boolean
): true | string {
  if (!value) return required ? 'Bitte eine URL angeben.' : true

  try {
    const url = new URL(value)
    if (!['http:', 'https:'].includes(url.protocol)) {
      return 'Nur HTTP- oder HTTPS-URLs sind erlaubt.'
    }
    if (url.username || url.password) {
      return 'Benutzername und Passwort gehören in die vorgesehenen Zugangsdatenfelder.'
    }
    return true
  } catch {
    return 'Bitte eine gültige URL eingeben.'
  }
}
