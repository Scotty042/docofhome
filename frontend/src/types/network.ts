export type NetworkRole =
  | 'router'
  | 'firewall'
  | 'switch'
  | 'access_point'
  | 'server'
  | 'nas'
  | 'client'
  | 'iot'
  | 'printer'
  | 'controller'
  | 'other'

export type NetworkInterfaceType = 'ethernet' | 'wifi' | 'fiber' | 'virtual' | 'cellular' | 'other'
export type NetworkPoeMode = 'none' | 'source' | 'sink' | 'passive' | 'unknown'
export type NetworkAssignmentType = 'static' | 'dhcp' | 'reservation' | 'link_local' | 'unknown'
export type NetworkConnectionType = 'physical' | 'logical' | 'wireless'
export type NetworkConnectionStatus = 'active' | 'planned' | 'inactive'

export type NetworkIpStatus = 'match' | 'mismatch' | 'not_detected' | 'observed_only' | 'conflict' | 'no_integration'

export interface NetworkIpOverview {
  key: string
  status: NetworkIpStatus
  device_id: string | null
  device_name: string
  interface_id: string | null
  interface_name: string | null
  documented_address_id: string | null
  documented_address: string | null
  mac_address: string | null
  assignment_type: NetworkAssignmentType
  observed_address_id: string | null
  observed_address: string | null
  source: string | null
  last_seen_at: string | null
  ignored: boolean
}

export interface NetworkDevice {
  id: string
  asset_id: string
  asset_name: string
  asset_code: string
  asset_type: string
  switch_port_layout: 'odd_even' | 'sequential_halves'
  product_name: string | null
  location_name: string | null
  role: NetworkRole
  hostname: string | null
  management_url: string | null
  notes: string | null
  primary_address: string | null
  interface_count: number
  address_count: number
  connection_count: number
  archived: boolean
  created_at: string
  updated_at: string
}

export interface NetworkDeviceWrite {
  asset_id: string
  role: NetworkRole
  hostname: string | null
  management_url: string | null
  notes: string | null
}

export interface NetworkDeviceCandidate {
  asset_id: string
  name: string
  jarvis_code: string
  asset_type: string
  product_name: string | null
  location_name: string | null
}

export interface NetworkSegment {
  id: string
  name: string
  cidr: string
  vlan_id: number | null
  gateway: string | null
  dns_servers: string[]
  description: string | null
  address_count: number
  created_at: string
  updated_at: string
}

export interface NetworkSegmentWrite {
  name: string
  cidr: string
  vlan_id: number | null
  gateway: string | null
  dns_servers: string[]
  description: string | null
}

export interface NetworkInterface {
  id: string
  network_device_id: string
  device_name: string
  name: string
  interface_type: NetworkInterfaceType
  mac_address: string | null
  speed_mbps: number | null
  poe_mode: NetworkPoeMode
  enabled: boolean
  is_primary: boolean
  logical_interface_id: string | null
  logical_interface_name: string | null
  member_count: number
  description: string | null
  address_count: number
  connection_count: number
  created_at: string
  updated_at: string
}

export interface NetworkInterfaceWrite {
  network_device_id: string
  name: string
  interface_type: NetworkInterfaceType
  mac_address: string | null
  speed_mbps: number | null
  poe_mode: NetworkPoeMode
  enabled: boolean
  is_primary: boolean
  logical_interface_id: string | null
  description: string | null
}

export interface NetworkAddress {
  id: string
  interface_id: string
  interface_name: string
  network_device_id: string
  device_name: string
  segment_id: string | null
  segment_name: string | null
  address: string
  assignment_type: NetworkAssignmentType
  hostname: string | null
  is_primary: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface NetworkAddressWrite {
  interface_id: string
  segment_id: string | null
  address: string
  assignment_type: NetworkAssignmentType
  hostname: string | null
  is_primary: boolean
  notes: string | null
}

export interface NetworkConnection {
  id: string
  source_interface_id: string
  source_interface_name: string
  source_device_id: string
  source_device_name: string
  target_interface_id: string
  target_interface_name: string
  target_device_id: string
  target_device_name: string
  connection_type: NetworkConnectionType
  status: NetworkConnectionStatus
  cable_type: string | null
  cable_label: string | null
  description: string | null
  created_at: string
  updated_at: string
}

export interface NetworkConnectionWrite {
  source_interface_id: string
  target_interface_id: string
  connection_type: NetworkConnectionType
  status: NetworkConnectionStatus
  cable_type: string | null
  cable_label: string | null
  description: string | null
}

export interface NetworkSummary {
  device_count: number
  segment_count: number
  interface_count: number
  address_count: number
  connection_count: number
  free_interface_count: number
  device_without_connection_count: number
  unconnected_interface_count: number
}

export interface NetworkTopologyNode {
  id: string
  asset_id: string
  name: string
  role: NetworkRole
  hostname: string | null
  location_name: string | null
  interface_count: number
}

export interface NetworkTopologyEdge {
  id: string
  source_device_id: string
  target_device_id: string
  source_label: string
  target_label: string
  connection_type: NetworkConnectionType
  status: NetworkConnectionStatus
  cable_label: string | null
}

export interface NetworkTopology {
  nodes: NetworkTopologyNode[]
  edges: NetworkTopologyEdge[]
}

export const networkRoleLabels: Record<NetworkRole, string> = {
  router: 'Router',
  firewall: 'Firewall',
  switch: 'Switch',
  access_point: 'Access Point',
  server: 'Server',
  nas: 'NAS',
  client: 'Client',
  iot: 'IoT-Gerät',
  printer: 'Drucker',
  controller: 'Controller',
  other: 'Sonstiges'
}

export const networkRoleIcons: Record<NetworkRole, string> = {
  router: 'mdi-router-network',
  firewall: 'mdi-shield-lock-outline',
  switch: 'mdi-switch',
  access_point: 'mdi-access-point',
  server: 'mdi-server',
  nas: 'mdi-nas',
  client: 'mdi-laptop',
  iot: 'mdi-chip',
  printer: 'mdi-printer-outline',
  controller: 'mdi-tune-variant',
  other: 'mdi-lan-connect'
}
