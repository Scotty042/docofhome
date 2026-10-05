export interface LegoSetWrite {
  set_number: string
  name: string
  theme: string
  release_year: number | null
  parts_count: number | null
  image_url: string | null
  location_id: string | null
  storage_note: string
  condition: string
  build_status: 'built' | 'disassembled' | 'sealed'
  complete: boolean | null
  box_present: boolean | null
  instructions_present: boolean | null
  purchase_date: string | null
  purchase_price: string | number | null
  seller: string
  width_cm: number | null
  depth_cm: number | null
  height_cm: number | null
  dimensions_note: string
  source_url: string | null
  researched_at: string | null
  notes: string
}
export interface LegoSet extends LegoSetWrite {
  id: string
  location_name: string | null
  created_at: string
  updated_at: string
}
export interface LegoDashboard {
  sets_count: number
  purchase_total: string
  currency: 'EUR'
  missing_prices: number
  parts_total: number
  missing_parts: number
}
export const buildStatuses = [
  { title: 'Aufgebaut', value: 'built' },
  { title: 'Zerlegt', value: 'disassembled' },
  { title: 'Ungeöffnet', value: 'sealed' }
]
export function emptyLegoSet(): LegoSetWrite {
  return { set_number: '', name: '', theme: '', release_year: null, parts_count: null,
    image_url: null, location_id: null, storage_note: '', condition: '', build_status: 'disassembled',
    complete: null, box_present: null, instructions_present: null, purchase_date: null,
    purchase_price: null, seller: '', width_cm: null, depth_cm: null, height_cm: null,
    dimensions_note: '', source_url: null, researched_at: null, notes: '' }
}
export function editableLegoSet(set: LegoSet): LegoSetWrite {
  return Object.fromEntries(Object.keys(emptyLegoSet()).map(key => [key, set[key as keyof LegoSetWrite]])) as unknown as LegoSetWrite
}
export function legoDimensions(set: LegoSetWrite): string {
  if ([set.width_cm, set.depth_cm, set.height_cm].every(v => v === null)) return 'Maße nicht erfasst'
  return [set.width_cm, set.depth_cm, set.height_cm].map(v => v === null ? '–' : v.toLocaleString('de-DE')).join(' × ') + ' cm (B × T × H)'
}
