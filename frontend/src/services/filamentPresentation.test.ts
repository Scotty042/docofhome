import { describe, expect, it } from 'vitest'
import { emptySpool, type FilamentSlot, type FilamentSpool } from '../types/filament'
import { filamentChoice, presentFilamentSlots } from './filamentPresentation'
const spool = (id: string, changes: Partial<FilamentSpool> = {}): FilamentSpool => ({ ...emptySpool(), id, label_code: `FIL-${id}`, manufacturer: 'Bambu Lab', variant: 'PLA Basic', color_name: 'Magenta', color_hex: '#EC008C', archived_at: null, ...changes } as FilamentSpool)
const slot = (changes: Partial<FilamentSlot> = {}): FilamentSlot => ({ id: 'slot-a', printer_serial: 'printer-a', ams_id: '0', slot_id: '0', spool_id: 'a', spool_label: 'FIL-a', rfid: null, tag_uid: null, material: 'PLA', color_hex: '#EC008C', remaining_percent: 0, occupied: true, manual_binding: false, observed_at: '2026-10-30T10:00:00Z', ...changes })
describe('AMS inventory presentation', () => {
  it('uses the bound ID to distinguish identical-colored physical spools and preserves zero', () => {
    const wrong=spool('other',{manufacturer:'Other'}),right=spool('a',{remaining_g:0})
    const card=presentFilamentSlots([slot()],[wrong,right])[0].slots[0]
    expect(card.spool).toBe(right);expect(card.title).toBe('Bambu Lab · PLA Basic');expect(card.colorName).toBe('Magenta');expect(card.spool?.remaining_g).toBe(0);expect(card.slot.remaining_percent).toBe(0)
  })
  it('does not guess from matching material, color or label', () => {
    const card=presentFilamentSlots([slot({spool_id:null})],[spool('a')])[0].slots[0]
    expect(card.spool).toBeNull();expect(card.title).toBe('Rolle noch nicht zugeordnet')
  })
  it('handles empty slots and missing or archived inventory spools', () => {
    for(const changes of [{occupied:false},{spool_id:'missing'}])expect(presentFilamentSlots([slot(changes)],[spool('a')])[0].slots[0].spool).toBeNull()
    expect(presentFilamentSlots([slot()],[spool('a',{archived_at:'2026-10-29'})])[0].slots[0].spool).toBeNull()
    expect(presentFilamentSlots([slot({occupied:false})],[spool('a')])[0].slots[0].title).toBe('Leer gemeldet')
  })
  it('uses safe colors and groups printers without conflating their slots', () => {
    const result=presentFilamentSlots([slot(),slot({id:'b',printer_serial:'printer-b'})],[spool('a',{color_name:'',color_hex:'invalid'})])
    expect(result.map(p=>p.serial)).toEqual(['printer-a','printer-b']);expect(result[0].slots[0].color).toBe('#808080')
    expect(filamentChoice(spool('a'))).toBe('Bambu Lab · PLA Basic · Magenta · FIL-a')
  })
})
