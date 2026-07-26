import type { DocumentEntryType } from '../types/documents'

function normalized(path: string): string {
  return path.trim().replace(/^\/+|\/+$/g, '')
}

export function folderPathChain(path: string): string[] {
  const cleanPath = normalized(path)
  if (!cleanPath) return ['']
  const parts = cleanPath.split('/').filter(Boolean)
  return [
    '',
    ...parts.map((_, index) => parts.slice(0, index + 1).join('/'))
  ]
}

export function isEqualOrDescendantPath(candidatePath: string, parentPath: string): boolean {
  const candidate = normalized(candidatePath)
  const parent = normalized(parentPath)
  if (!parent) return true
  return candidate === parent || candidate.startsWith(`${parent}/`)
}

export function isInvalidMoveDestination(
  sourcePath: string,
  sourceType: DocumentEntryType,
  candidatePath: string
): boolean {
  return sourceType === 'folder' && isEqualOrDescendantPath(candidatePath, sourcePath)
}
