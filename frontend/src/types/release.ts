export interface DashboardCardSetting {
  id: 'documentation' | 'consumption_comparison' | 'maintenance' | 'quality' | 'network'
  visible: boolean
}

export interface DashboardSetting {
  cards: DashboardCardSetting[]
  updated_at: string
}

export interface AuditEvent {
  id: string
  object_type: string
  object_id: string
  object_label: string | null
  object_route: string | null
  action: string
  change: Record<string, unknown>
  display_change: Record<string, unknown> | null
  created_at: string
}


export interface FritzBoxDevice {
  name: string
  mac_address: string | null
  ipv4: string | null
  ipv6: string | null
  active: boolean
  interface_type: string | null
  connection_rate_mbps: number | null
  connected_via: string | null
  last_seen: string | null
  dhcp_reservation: boolean | null
}

export interface ImportPreview {
  format: string
  export_version: string | null
  record_counts: Record<string, number>
  conflicts: string[]
  warnings: string[]
  writable: false
}

export interface ImportResult {
  created: number
  skipped: number
  conflicts: number
  modules: string[]
  rolled_back: boolean
}

export interface GuidedSetupDraftWrite {
  name: string
  current_step: number
  data: Record<string, unknown>
}

export interface GuidedSetupDraft extends GuidedSetupDraftWrite {
  id: string
  status: 'draft' | 'applied'
  created_at: string
  updated_at: string
}

export interface GuidedSetupPreview {
  draft_id: string
  actions: string[]
  warnings: string[]
  errors: string[]
  duplicate_asset_ids: string[]
  can_apply: boolean
}

export interface GuidedSetupApply {
  draft_id: string
  asset_id: string
  created_object_ids: string[]
  applied_at: string
}

export interface PortGroupWrite {
  group: 'copper' | 'sfp' | 'sfp_plus' | 'uplink'
  count: number
  scheme: 'numeric' | 'gigabit' | 'ethernet'
  start: number
  speed_mbps: number | null
  poe_capable: boolean
}

export interface PortGenerationPreview {
  device_id: string
  existing_names: string[]
  create_names: string[]
  unchanged_names: string[]
  requested_total: number
  created?: number
}

export interface NetworkPath {
  target_device_id: string
  nodes: Array<{ device_id: string; asset_id: string; name: string; role: string }>
  connection_ids: string[]
  warnings: string[]
  documented_path: true
}

export interface ServiceWorkloadWrite {
  host_asset_id: string
  name: string
  image: string | null
  image_tag: string | null
  compose_project: string | null
  network_mode: 'bridge' | 'host' | 'macvlan' | 'docker_network'
  macvlan_address: string | null
  ports: Array<{ container_port: number; host_port: number | null; protocol: 'tcp' | 'udp' }>
  urls: {
    internal: string | null
    external: string | null
    administrative: string | null
    api: string | null
  }
  reverse_proxy: string | null
  dependency_ids: string[]
  status: 'running' | 'stopped' | 'planned' | 'unknown'
  notes: string | null
}

export interface ServiceWorkload extends ServiceWorkloadWrite {
  id: string
  host_name: string
  docker_container_id: string | null
  docker_status_text: string | null
  docker_networks: string[]
  docker_mounts: string[]
  docker_last_seen_at: string | null
  docker_managed: boolean
  created_at: string
  updated_at: string
}

export interface DockerSyncSettingWrite {
  enabled: boolean
  socket_path: string
  host_asset_id: string | null
  refresh_interval_seconds: 0 | 30 | 60 | 300 | 900 | 1800
}

export interface DockerSyncSetting extends DockerSyncSettingWrite {
  host_name: string | null
  last_attempt_at: string | null
  last_success_at: string | null
  last_error: string | null
}

export interface DockerSyncResult {
  imported: number
  updated: number
  missing: number
  total: number
  docker_version: string | null
  synchronized_at: string
}

export interface DockerConnectionTest {
  success: boolean
  message: string
  docker_version: string | null
}
