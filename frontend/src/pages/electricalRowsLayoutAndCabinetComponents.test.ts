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

  it('materializes N and PE areas as editable wiring endpoints', () => {
    expect(layout).toContain('cabinetComponentAreaOptions')
    expect(layout).toContain("area.area_type === 'neutral_rail'")
    expect(layout).toContain("area.area_type === 'protective_earth_rail'")
    expect(layout).toContain('Diesen Bereich als verkabelbare Schiene anlegen')
    expect(layout).toContain('Noch nicht als elektrischer Endpunkt angelegt.')
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
    expect(layout).toContain('excludeDeviceId !== null || excludeAssetId !== null')
  })

  it('renders one-TE devices with a reliable vertical compact label', () => {
    expect(layout).toContain(
      "'narrow-module-device': viewMode === 'compact' && placement.device.module_width === 1"
    )
    expect(layout).toContain(
      "'narrow-module-device': viewMode === 'compact' && placement.module_width === 1"
    )
    expect(layout).toContain('class="module-device-name"')
    expect(layout).toContain('writing-mode: vertical-rl')
    expect(layout).toContain('transform: rotate(180deg)')
  })

  it('keeps cabinet component validation errors inside the open dialog', () => {
    expect(layout).toContain('const cabinetComponentError = ref<string | null>(null)')
    expect(layout).toContain('v-if="cabinetComponentError"')
    expect(layout).toContain('{{ cabinetComponentError }}')
    expect(layout).toContain('cabinetComponentError.value = reason instanceof Error')
  })

})
