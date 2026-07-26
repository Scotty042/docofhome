import type {
  BackupListRead,
  BackupRecord,
  BackupRestoreRead,
  BackupSchedule,
  BackupScheduleWrite,
  BackupValidationRead,
  RemoteBackupListRead
} from '../types/backups'

const basePath = '/api/v1/backups'

async function errorMessage(response: Response): Promise<string> {
  let message = `Anfrage fehlgeschlagen (HTTP ${response.status})`
  try {
    const body = await response.json() as { detail?: string }
    if (body.detail) message = body.detail
  } catch {
    // Keep the HTTP fallback.
  }
  return message
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${basePath}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  return response.json() as Promise<T>
}

function remotePath(folder: string): string {
  return `?folder=${encodeURIComponent(folder)}`
}

export const backupApi = {
  list: () => request<BackupListRead>(''),
  create: (uploadToNextcloud: boolean, nextcloudFolder: string) => request<BackupRecord>('', {
    method: 'POST',
    body: JSON.stringify({
      upload_to_nextcloud: uploadToNextcloud,
      nextcloud_folder: nextcloudFolder
    })
  }),
  importArchive: async (file: File): Promise<BackupRecord> => {
    const response = await fetch(`${basePath}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/zip' },
      body: file
    })
    if (!response.ok) throw new Error(await errorMessage(response))
    return response.json() as Promise<BackupRecord>
  },
  listRemote: (folder: string) => request<RemoteBackupListRead>(
    `/remote${remotePath(folder)}`
  ),
  importRemote: (filename: string, folder: string) => request<BackupRecord>(
    `/remote/${encodeURIComponent(filename)}/import${remotePath(folder)}`,
    { method: 'POST' }
  ),
  removeRemote: async (filename: string, folder: string): Promise<void> => {
    const response = await fetch(
      `${basePath}/remote/${encodeURIComponent(filename)}${remotePath(folder)}`,
      { method: 'DELETE' }
    )
    if (!response.ok) throw new Error(await errorMessage(response))
  },
  readSchedule: () => request<BackupSchedule>('/schedule'),
  updateSchedule: (schedule: BackupScheduleWrite) => request<BackupSchedule>('/schedule', {
    method: 'PUT', body: JSON.stringify(schedule)
  }),
  runScheduleNow: () => request<BackupSchedule>('/schedule/run', { method: 'POST' }),
  downloadUrl: (filename: string) => `${basePath}/${encodeURIComponent(filename)}/download`,
  remove: async (filename: string): Promise<void> => {
    const response = await fetch(`${basePath}/${encodeURIComponent(filename)}`, {
      method: 'DELETE'
    })
    if (!response.ok) throw new Error(await errorMessage(response))
  },
  validate: (filename: string) => request<BackupValidationRead>(
    `/${encodeURIComponent(filename)}/validate`,
    { method: 'POST' }
  ),
  restore: (filename: string, confirmation: string) => request<BackupRestoreRead>(
    `/${encodeURIComponent(filename)}/restore`,
    { method: 'POST', body: JSON.stringify({ confirmation }) }
  )
}
