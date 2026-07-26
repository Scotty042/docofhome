import duplicateDialog from '../components/AssetDuplicateDialog.vue?raw'
import layout from './ElectricalDistributionLayoutPage.vue?raw'
import topology from '../services/electricalTopology.ts?raw'
import { describe, expect, it } from 'vitest'

describe('simple electrical rows and passive cabinet components', () => {
  it('supports rows placement without requesting a fields layout', () => {
    expect(duplicateDialog).toContain("selectedUsesSections")
    expect(duplicateDialog).toContain("area_id: placeSequentially.value && selectedUsesSections.value")
    expect(duplicateDialog).toContain('Diese Verteilung verwendet die einfache Reihenaufteilung')
    expect(layout).toContain('dropDeviceSimple')
    expect(layout).toContain('area_id: structuredLayout.value ? placementForm.value.area_id : null')
    expect(layout).toContain('v-if="structuredLayout" v-model="placementForm.area_id"')
  })

  it('offers non-asset cabinet components as wiring endpoints', () => {
    expect(layout).toContain('Phasenverteilerblock L1/L2/L3')
    expect(layout).toContain('endpoint-kind="cabinet_component"')
    expect(layout).toContain('Verteilerblöcke, Sammelschienen und Klemmen sind interne Schrankobjekte')
    expect(topology).toContain("cabinet_component: 'Schrankkomponente'")
    expect(topology).toContain("cabinet_component: 'mdi-call-split'")
  })
  it('shows private FI groups, neutral rails and busbar phase patterns', () => {
    expect(layout).toContain('Zugehöriger FI/RCD')
    expect(layout).toContain('Startphase')
    expect(layout).toContain('busbarPhasePattern(component)')
    expect(layout).toContain('effective_rcd_name')
    expect(layout).toContain('effective_neutral_rail_name')
    expect(layout).toContain('Kompakt')
    expect(layout).toContain('Erweitert')
    expect(layout).toContain('detailDrawer')
  })

  it('renders and moves normal DIN assets in both rows and fields layouts', () => {
    expect(layout).toContain('beginAssetDrag')
    expect(layout).toContain('draggedAsset')
    expect(layout).toContain('electricalApi.placeAsset')
    expect(layout).toContain('simpleAssetPlacementsForRow')
    expect(layout).toContain('assetPlacementsForArea(area.id).filter')
    expect(layout).toContain('Noch nicht platzierte DIN-Assets')
    expect(layout).toContain('asset.effective_module_width')
  })

})
