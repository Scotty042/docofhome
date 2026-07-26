import source from './AboutPage.vue?raw'
import markdownSource from '../components/SafeMarkdown.vue?raw'
import dashboardSource from './DashboardPage.vue?raw'
import consumptionSource from './ConsumptionPage.vue?raw'
import settingsSource from './SettingsPage.vue?raw'
import { describe, expect, it } from 'vitest'

describe('about page and mobile reading shortcut', () => {
  it('shows central versions, source-controlled links and active ZIP feedback', () => {
    expect(source).toContain('Versionen & Changelog')
    expect(source).toContain('information.version')
    expect(source).not.toContain('Impressum')
    expect(source).toContain('öffentlichen DocOfHome-File-Drop')
    expect(source).toContain('feedback.include_technical_info')
    expect(source).toContain('Tokens, Passwörter und Konfigurationen werden nicht übertragen')
    expect(settingsSource).not.toContain('form.about')
    expect(settingsSource).not.toContain('Impressum')
    expect(settingsSource).toContain('const integrationMeta:')
    expect(settingsSource).toContain('const requiredRule =')
    expect(markdownSource).not.toContain('v-html')
  })

  it('replaces the version tile with a direct meter-reading action', () => {
    expect(dashboardSource).toContain('Zählerstände erfassen')
    expect(dashboardSource).toContain('/consumption?capture=1')
    expect(dashboardSource).not.toContain('Installierte Version')
    expect(consumptionSource).toContain("route.query.capture === '1'")
  })
})
