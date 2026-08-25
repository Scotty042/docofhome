export type SetupAvailability = boolean | 'unavailable'

export type SetupNavigationDecision = true | {
  name: 'dashboard' | 'setup' | 'unavailable'
  query?: { from: string }
}

export function resolveSetupNavigation(
  targetName: string,
  targetPath: string,
  availability: SetupAvailability
): SetupNavigationDecision {
  if (availability === 'unavailable') {
    if (targetName === 'unavailable') return true
    return { name: 'unavailable', query: { from: targetPath } }
  }

  if (!availability) {
    return targetName === 'setup' ? true : { name: 'setup' }
  }

  if (targetName === 'setup' || targetName === 'unavailable') {
    return { name: 'dashboard' }
  }
  return true
}
