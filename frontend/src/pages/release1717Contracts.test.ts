import { describe, expect, it } from 'vitest'

import consumption from './ConsumptionPage.vue?raw'
import maintenance from './MaintenancePage.vue?raw'
import settings from './SettingsPage.vue?raw'
import readme from '../../../README.md?raw'

describe('release 1.7.17 mobile fixes and integration URLs', () => {
  it('keeps mobile dialogs and consumption charts usable', () => {
    expect(maintenance).toContain('aria-label="Lebenslauf schließen"')
    expect(maintenance).toContain(':fullscreen="smAndDown"')
    expect(consumption).toContain('currentLocalDateTime()')
    expect(consumption).toContain('<v-window v-model="tab" :touch="false">')
    expect(consumption).toContain('touch-action: pan-x')
  })

  it('separates internal integration URLs from browser links', () => {
    expect(settings).toContain('Interne Server-URL')
    expect(settings).toContain('Browser-URL')
    expect(settings).toContain("integration.kind === 'immich' || integration.kind === 'paperless'")
  })

  it('ships the rewritten GitHub presentation with current screenshots', () => {
    expect(readme).toContain('die persönliche Dokumentation für das eigene Zuhause')
    expect(readme).toContain('docs/screenshots/dashboard.png')
    expect(readme).toContain('docs/screenshots/electrical-distribution.png')
    expect(readme).toContain('ChatGPT und andere Assistenten über MCP anbinden')
  })
})
