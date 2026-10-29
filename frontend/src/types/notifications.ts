export type PushProvider = 'pushover' | 'ntfy'
export interface PushConfig {
  enabled: boolean
  readings_enabled: boolean
  maintenance_enabled: boolean
  tasks_enabled: boolean
  send_hour: number
  send_minute: number
  days_ahead: number
  public_url: string | null
  pushover_enabled: boolean
  pushover_device: string
  ntfy_enabled: boolean
  ntfy_url: string
  ntfy_topic: string
}
export interface PushWrite extends PushConfig {
  pushover_app_token?: string
  pushover_user_key?: string
  ntfy_access_token?: string
  clear_pushover_app_token?: boolean
  clear_pushover_user_key?: boolean
  clear_ntfy_access_token?: boolean
}
export interface PushRead extends PushConfig {
  pushover_app_token_configured: boolean
  pushover_user_key_configured: boolean
  ntfy_access_token_configured: boolean
}
export interface PushDelivery {
  provider: PushProvider
  kind: string
  status: string
  attempts: number
  detail: string | null
  last_attempt_at: string | null
  next_retry_at: string | null
}
export function defaultPushConfig(): PushWrite {
  return { enabled: false, readings_enabled: true, maintenance_enabled: true, tasks_enabled: true,
    send_hour: 8, send_minute: 0, days_ahead: 3, public_url: null,
    pushover_enabled: false, pushover_device: '', ntfy_enabled: false,
    ntfy_url: 'https://ntfy.sh', ntfy_topic: '' }
}
export function editablePushConfig(data: PushRead): PushWrite {
  return Object.fromEntries(Object.keys(defaultPushConfig()).map(key => [key, data[key as keyof PushConfig]])) as unknown as PushWrite
}
