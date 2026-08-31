import { describe, expect, it } from 'vitest'

import maintenance from './MaintenancePage.vue?raw'
import settings from './SettingsPage.vue?raw'
import workTypes from '../types/work.ts?raw'
import paperlessApi from '../services/paperlessApi.ts?raw'

describe('release 1.7.15 maintenance life records and Paperless links', () => {
  it('adds structured subject profiles and a cross-activity timeline', () => {
    expect(maintenance).toContain('Lebenslauf')
    expect(maintenance).toContain('FIN / Fahrzeug-Identifizierungsnummer')
    expect(maintenance).toContain('Schornsteinfeger')
    expect(maintenance).toContain('Impfung')
    expect(maintenance).toContain('Messung / Gewicht / Zählerstand')
    expect(workTypes).toContain('WorkSubjectTimeline')
  })

  it('adds a manual Paperless document picker without copying PDFs', () => {
    expect(settings).toContain("name: 'Paperless-ngx'")
    expect(settings).toContain("secretLabel: 'API-Token'")
    expect(maintenance).toContain('Paperless-Dokument verknüpfen')
    expect(maintenance).toContain('keine PDF-Kopie')
    expect(paperlessApi).toContain('/api/v1/paperless')
  })
})
