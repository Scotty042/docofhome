import source from './ConsumptionPage.vue?raw'
import { describe, expect, it } from 'vitest'

describe('mobile meter reading dialog', () => {
  it('keeps input on save errors and prevents duplicate submits', () => {
    const saveReading = source.slice(
      source.indexOf('async function saveReading()'),
      source.indexOf('async function archiveReading')
    )

    expect(saveReading.indexOf('readingDialog.value = false')).toBeGreaterThan(
      saveReading.indexOf('await consumptionApi')
    )
    expect(saveReading).toContain("setError(reason, 'Ablesung konnte nicht gespeichert werden.')")
    expect(source).toContain(':disabled="saving || !readingForm.meter_id"')
    expect(source).toContain("notifications.error(message)")
    expect(source).toContain('Aktueller Monat · bis heute')
  })
})
