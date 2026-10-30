import type { FilamentSlot, FilamentSpool } from '../types/filament'

export function filamentTitle(spool: FilamentSpool): string {
  return [spool.manufacturer.trim(), (spool.variant || spool.material).trim()].filter(Boolean).join(' · ') || 'Lagerrolle'
}

export function filamentChoice(spool: FilamentSpool): string {
  return [filamentTitle(spool), spool.color_name || spool.color_hex, spool.label_code].filter(Boolean).join(' · ')
}

export function presentFilamentSlots(slots: FilamentSlot[], spools: FilamentSpool[]) {
  const byId = new Map(spools.map(spool => [spool.id, spool]))
  const printers = new Map<string, { serial: string; slots: Array<{
    slot: FilamentSlot; spool: FilamentSpool | null; title: string; color: string; colorName: string
  }> }>()
  for (const slot of slots) {
    // Only an existing explicit ID binding identifies a physical inventory spool.
    const found = slot.occupied && slot.spool_id ? byId.get(slot.spool_id) : undefined
    const spool = found && !found.archived_at ? found : null
    const rawColor = spool?.color_hex || slot.color_hex
    const color = /^#[a-f\d]{6}(?:[a-f\d]{2})?$/i.test(rawColor) ? rawColor : '#808080'
    const entry = {
      slot, spool, color,
      title: !slot.occupied ? 'Leer gemeldet' : spool ? filamentTitle(spool) : 'Rolle noch nicht zugeordnet',
      colorName: spool?.color_name.trim() || (slot.occupied ? (/^#[a-f\d]{6}(?:[a-f\d]{2})?$/i.test(rawColor) ? rawColor : 'Farbe unbekannt') : 'Keine Rolle')
    }
    if (!printers.has(slot.printer_serial)) printers.set(slot.printer_serial, { serial: slot.printer_serial, slots: [] })
    printers.get(slot.printer_serial)!.slots.push(entry)
  }
  return [...printers.values()]
}
