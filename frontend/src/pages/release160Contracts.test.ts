import { describe, expect, it } from 'vitest'

import measurementCard from '../components/SmartMeterMeasurementPointsCard.vue?raw'
import handbook from '../content/handbook.ts?raw'
import guidedSetup from './GuidedSetupPage.vue?raw'
import layout from './ElectricalDistributionLayoutPage.vue?raw'
import masterData from './MasterDataPage.vue?raw'
import setupWizard from './SetupWizardPage.vue?raw'


describe('DocOfHome 1.6.0 release contracts', () => {
  it('clears integration feedback when the setup wizard changes service', () => {
    expect(setupWizard).toContain('watch(currentStep')
    expect(setupWizard).toContain('integrationTestResult.value = null')
    expect(setupWizard).toContain('testingIntegration.value = false')
  })

  it('finishes guided setup with redirect and a manual fallback', () => {
    expect(guidedSetup).toContain("name: 'asset-detail'")
    expect(guidedSetup).toContain('Asset öffnen')
    expect(guidedSetup).toContain('redirectFailed')
    expect(guidedSetup).toContain('saving.value || applied.value')
  })

  it('prioritises a compact desktop and tablet cabinet view', () => {
    expect(layout).toContain('Noch nicht platzierte DIN-Assets')
    expect(layout).toContain('isElectricalConsumptionMeterType')
    expect(layout).toContain('isNonElectricalMeterAssetType')
    expect(layout).toContain('cabinet-type-smart-meter')
    expect(layout).toContain('cabinet-type-impulse-switch')
    expect(layout).toContain('technical_short_label')
    expect(layout).toContain('cabinet-legend')
    expect(layout).toContain('text-overflow: ellipsis')
  })

  it('offers B16 defaults and the standard impulse switch type', () => {
    expect(masterData).toContain("name: 'Sicherungsautomat'")
    expect(masterData).toContain("breaker_characteristic: 'B'")
    expect(masterData).toContain('rated_current_a: 16')
    expect(masterData).toContain("name: 'Stromstoßschalter'")
    expect(masterData).toContain('coil_voltage_v: 230')
    expect(masterData).toContain("contact_type: 'normally_open'")
  })

  it('documents CT clamps as non-conductive measurement points with HA entities', () => {
    expect(measurementCard).toContain('Gemessene Verkabelung')
    expect(measurementCard).toContain('Home-Assistant-Entitäten')
    expect(measurementCard).toContain('Sie erzeugen keine neue stromführende Verbindung')
    expect(handbook).toContain("term: 'Stromwandlerklemme / CT-Klemme'")
  })

  it('explains the scope difference between busbar and comb busbar', () => {
    expect(handbook).toContain('Nicht jede Sammelschiene ist eine Kammschiene')
    expect(handbook).toContain('direkt nebeneinanderliegende Reiheneinbaugeräte')
    expect(handbook).toContain('mehrere FI-Gruppen')
  })
})
