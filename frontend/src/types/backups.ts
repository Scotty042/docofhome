export type BackupRecord = {
  filename: string
  created_at: string
  size_bytes: number
  sha256: string
  database_size_bytes: number
  app_version: string
  nextcloud_uploaded: boolean
}

export type BackupListRead = { items: BackupRecord[] }

export type RemoteBackupRecord = {
  filename: string
  size_bytes: number
  modified_at: string | null
  local_available: boolean
}

export type RemoteBackupListRead = { items: RemoteBackupRecord[] }

export type BackupValidationRead = {
  valid: boolean
  message: string
  record: BackupRecord | null
}

export type BackupRestoreRead = {
  scheduled: boolean
  restart_required: boolean
  message: string
}

export type BackupSchedule = {
  enabled: boolean
  interval_hours: number
  retention_count: number
  upload_to_nextcloud: boolean
  nextcloud_folder: string
  last_attempt_at: string | null
  last_success_at: string | null
  last_error: string | null
}

export type BackupScheduleWrite = Pick<
  BackupSchedule,
  'enabled' | 'interval_hours' | 'retention_count' | 'upload_to_nextcloud' | 'nextcloud_folder'
>
