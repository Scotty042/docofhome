export interface SpoolWrite {
  manufacturer: string; material: string; variant: string; color_name: string; color_hex: string
  shop_code: string; condition: 'sealed' | 'open'; initial_g: number | null; remaining_g: number | null
  remaining_percent: number | null; location_id: string | null; storage_note: string
  reorder: boolean; reorder_note: string; notes: string; image_url: string | null; rfid: string | null
}
export interface FilamentSpool extends SpoolWrite {
  id: string; label_code: string; location_name: string | null; image_source_url: string | null
  image_verified: boolean; cloud_account: string | null; cloud_id: string | null
  cloud_present: boolean | null; cloud_sync_at: string | null; cloud_product_code: string
  printer_serial: string | null; ams_id: string | null; slot_id: string | null
  mount_source: string | null; mount_observed_at: string | null; last_seen_at: string | null
  archived_at: string | null; created_at: string; updated_at: string
}
export interface FilamentConfig { enabled: boolean; region: 'global' | 'cn'; interval_minutes: number; public_url: string | null; printer_serials: string[]; mqtt_enabled: boolean }
export interface FilamentSettings extends FilamentConfig { token_configured: boolean; last_sync: string | null; last_error: string | null; last_mqtt: string | null; mqtt_error: string | null }
export interface FilamentSlot { id: string; printer_serial: string; ams_id: string; slot_id: string; spool_id: string | null; spool_label: string | null; rfid: string | null; tag_uid: string | null; material: string; color_hex: string; remaining_percent: number | null; occupied: boolean; manual_binding: boolean; observed_at: string }
export function emptySpool(): SpoolWrite { return { manufacturer: '', material: 'PLA', variant: '', color_name: '', color_hex: '#808080', shop_code: '', condition: 'sealed', initial_g: null, remaining_g: null, remaining_percent: null, location_id: null, storage_note: '', reorder: false, reorder_note: '', notes: '', image_url: null, rfid: null } }
export function editableSpool(data: FilamentSpool): SpoolWrite { return Object.fromEntries(Object.keys(emptySpool()).map(key => [key, data[key as keyof SpoolWrite]])) as unknown as SpoolWrite }
export function emptyFilamentConfig(): FilamentConfig { return { enabled: false, region: 'global', interval_minutes: 30, public_url: null, printer_serials: [], mqtt_enabled: false } }
export function editableFilamentConfig(data: FilamentConfig): FilamentConfig { return Object.fromEntries(Object.keys(emptyFilamentConfig()).map(key => [key, data[key as keyof FilamentConfig]])) as unknown as FilamentConfig }
