<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AssetTypeIconPicker from '../components/AssetTypeIconPicker.vue'
import ProductImageField from '../components/ProductImageField.vue'
import { assetApi } from '../services/assetApi'
import type {
  AssetType,
  AssetTypeWrite,
  Label,
  LabelWrite,
  Product,
  ProductWrite
} from '../types/assets'

type MasterDataTab = 'asset-types' | 'products' | 'labels'
type FormHandle = { validate: () => Promise<{ valid: boolean }> }

interface ArchiveTarget {
  kind: MasterDataTab
  id: string
  name: string
}

const route = useRoute()
const router = useRouter()
const allowedTabs: MasterDataTab[] = ['asset-types', 'products', 'labels']
const requestedTab = String(route.query.tab ?? '') as MasterDataTab
const tab = ref<MasterDataTab>(allowedTabs.includes(requestedTab) ? requestedTab : 'asset-types')
const showArchived = ref(false)
const assetTypes = ref<AssetType[]>([])
const products = ref<Product[]>([])
const labels = ref<Label[]>([])
const loading = ref(true)
const saving = ref(false)
const importing = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const formElement = ref<FormHandle | null>(null)
const editorOpen = ref(false)
const editorKind = ref<MasterDataTab>('asset-types')
const editingId = ref<string | null>(null)
const archiveTarget = ref<ArchiveTarget | null>(null)
const assetTypeForm = ref<AssetTypeWrite>({ name: '', description: null, icon: null, module_width: null })
const productForm = ref<ProductWrite>({
  name: '',
  manufacturer: null,
  model_number: null,
  description: null,
  image_url: null,
  image_source: 'url',
  image_reference: null,
  din_rail_mount: false,
  module_width: null,
  asset_type_id: null
})
const labelForm = ref<LabelWrite>({ name: '', color: '#26c6da' })

const recommendedAssetTypes: AssetTypeWrite[] = [
  {
    name: 'Elektrische Verteilung',
    description: 'Haupt- und Unterverteilungen',
    icon: 'mdi-electric-switch',
    module_width: null
  },
  {
    name: 'Sicherungsautomat',
    description: 'Leitungsschutzschalter',
    icon: 'mdi-toggle-switch',
    module_width: 1
  },
  {
    name: 'FI-Schutzschalter',
    description: 'Fehlerstrom-Schutzschalter',
    icon: 'mdi-shield-outline',
    module_width: 4
  },
  {
    name: 'FI/LS-Schalter',
    description: 'Kombinierter Fehlerstrom- und Leitungsschutz',
    icon: 'mdi-shield-check',
    module_width: 2
  },
  {
    name: 'Stromzähler',
    description: 'Elektrischer Energiezähler',
    icon: 'mdi-meter-electric',
    module_width: null
  },
  {
    name: 'Wechselrichter',
    description: 'PV- oder Speicherwechselrichter',
    icon: 'mdi-solar-power-variant',
    module_width: null
  },
  {
    name: 'Batteriespeicher',
    description: 'Stationärer elektrischer Speicher',
    icon: 'mdi-battery-high',
    module_width: null
  },
  {
    name: 'Smart Meter',
    description: 'Digitaler Leistungs- und Energiezähler',
    icon: 'mdi-meter-electric-outline',
    module_width: 4
  },
  {
    name: 'Netzwerkgerät',
    description: 'Router, Switch, Access Point oder Firewall',
    icon: 'mdi-router-network',
    module_width: null
  },
  { name: 'Server', description: 'Physischer Server oder Host', icon: 'mdi-server', module_width: null },
  { name: 'NAS', description: 'Netzwerkspeicher', icon: 'mdi-nas', module_width: null },
  { name: 'Heizung', description: 'Heizungsanlage oder Wärmeerzeuger', icon: 'mdi-radiator', module_width: null },
  { name: 'Haushaltsgerät', description: 'Festes oder mobiles Haushaltsgerät', icon: 'mdi-washing-machine', module_width: null },
  { name: 'Sensor', description: 'Mess- oder Zustandsaufnehmer', icon: 'mdi-access-point', module_width: null },
  { name: 'Sonstiges Gerät', description: 'Allgemeiner Auffangtyp', icon: 'mdi-devices', module_width: null }
]
const editorTitle = computed(() => {
  const action = editingId.value ? 'bearbeiten' : 'anlegen'
  if (editorKind.value === 'asset-types') return `Asset-Typ ${action}`
  if (editorKind.value === 'products') return `Produkt ${action}`
  return `Label ${action}`
})
const activeAssetTypes = computed(() => assetTypes.value.filter((item) => !item.deleted_at))
const requiredRule = (value: string | null) => Boolean(value?.trim()) || 'Dieses Feld ist erforderlich.'
const colorRule = (value: string) => /^#[0-9a-fA-F]{6}$/.test(value) || 'Farbe als #RRGGBB angeben.'

watch(tab, (value) => {
  void router.replace({ query: { ...route.query, tab: value } })
})
watch(showArchived, () => void load())

onMounted(() => void load())

async function load() {
  loading.value = true
  error.value = null
  try {
    const [typeItems, productItems, labelItems] = await Promise.all([
      assetApi.allAssetTypes(showArchived.value),
      assetApi.allProducts(showArchived.value),
      assetApi.allLabels(showArchived.value)
    ])
    assetTypes.value = typeItems
    products.value = productItems
    labels.value = labelItems
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Stammdaten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function optionalText(value: string | null | undefined): string | null {
  return value?.trim() || null
}

function openCreate(kind: MasterDataTab) {
  editorKind.value = kind
  editingId.value = null
  assetTypeForm.value = { name: '', description: null, icon: null, module_width: null }
  productForm.value = {
    name: '',
    manufacturer: null,
    model_number: null,
    description: null,
    image_url: null,
    image_source: 'url',
    image_reference: null,
    din_rail_mount: false,
    module_width: null,
    asset_type_id: null
  }
  labelForm.value = { name: '', color: '#26c6da' }
  editorOpen.value = true
}

function editAssetType(item: AssetType) {
  editorKind.value = 'asset-types'
  editingId.value = item.id
  assetTypeForm.value = { name: item.name, description: item.description, icon: item.icon, module_width: item.module_width }
  editorOpen.value = true
}

function editProduct(item: Product) {
  editorKind.value = 'products'
  editingId.value = item.id
  productForm.value = {
    name: item.name,
    manufacturer: item.manufacturer,
    model_number: item.model_number,
    description: item.description,
    image_url: item.image_url ?? null,
    image_source: item.image_source,
    image_reference: item.image_reference,
    din_rail_mount: item.din_rail_mount,
    module_width: item.module_width,
    asset_type_id: item.asset_type_id
  }
  editorOpen.value = true
}

function editLabel(item: Label) {
  editorKind.value = 'labels'
  editingId.value = item.id
  labelForm.value = { name: item.name, color: item.color }
  editorOpen.value = true
}

async function saveEditor() {
  const validation = await formElement.value?.validate()
  if (validation && !validation.valid) return
  saving.value = true
  error.value = null
  success.value = null
  try {
    if (editorKind.value === 'asset-types') {
      const payload: AssetTypeWrite = {
        name: assetTypeForm.value.name.trim(),
        description: optionalText(assetTypeForm.value.description),
        icon: optionalText(assetTypeForm.value.icon),
        module_width: assetTypeForm.value.module_width
      }
      if (editingId.value) await assetApi.updateAssetType(editingId.value, payload)
      else await assetApi.createAssetType(payload)
    } else if (editorKind.value === 'products') {
      const payload: ProductWrite = {
        name: productForm.value.name.trim(),
        manufacturer: optionalText(productForm.value.manufacturer),
        model_number: optionalText(productForm.value.model_number),
        description: optionalText(productForm.value.description),
        image_url: optionalText(productForm.value.image_url),
        image_source: productForm.value.image_source,
        image_reference: optionalText(productForm.value.image_reference),
        din_rail_mount: productForm.value.din_rail_mount,
        module_width: productForm.value.din_rail_mount ? productForm.value.module_width : null,
        asset_type_id: productForm.value.asset_type_id || null
      }
      if (editingId.value) await assetApi.updateProduct(editingId.value, payload)
      else await assetApi.createProduct(payload)
    } else {
      const payload: LabelWrite = {
        name: labelForm.value.name.trim(),
        color: labelForm.value.color.toLowerCase()
      }
      if (editingId.value) await assetApi.updateLabel(editingId.value, payload)
      else await assetApi.createLabel(payload)
    }
    editorOpen.value = false
    success.value = 'Stammdatum wurde gespeichert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Stammdatum konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

function askArchive(kind: MasterDataTab, id: string, name: string) {
  archiveTarget.value = { kind, id, name }
}

async function confirmArchive() {
  const target = archiveTarget.value
  if (!target) return
  saving.value = true
  error.value = null
  success.value = null
  try {
    if (target.kind === 'asset-types') await assetApi.removeAssetType(target.id)
    else if (target.kind === 'products') await assetApi.removeProduct(target.id)
    else await assetApi.removeLabel(target.id)
    archiveTarget.value = null
    success.value = 'Stammdatum wurde archiviert.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Stammdatum konnte nicht archiviert werden.'
  } finally {
    saving.value = false
  }
}

async function addRecommendedAssetTypes() {
  importing.value = true
  error.value = null
  success.value = null
  let created = 0
  try {
    const existingNames = new Set(
      activeAssetTypes.value.map((item) => item.name.trim().toLocaleLowerCase('de-DE'))
    )
    for (const recommendation of recommendedAssetTypes) {
      const normalized = recommendation.name.toLocaleLowerCase('de-DE')
      if (existingNames.has(normalized)) continue
      await assetApi.createAssetType(recommendation)
      existingNames.add(normalized)
      created += 1
    }
    success.value = created > 0
      ? `${created} empfohlene Asset-Typen wurden angelegt.`
      : 'Alle empfohlenen Asset-Typen sind bereits vorhanden.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error
      ? `Empfohlene Typen wurden nur teilweise angelegt: ${reason.message}`
      : 'Empfohlene Typen konnten nicht vollständig angelegt werden.'
    await load()
  } finally {
    importing.value = false
  }
}

function assetTypeName(id: string | null): string {
  if (!id) return 'Alle Typen'
  return assetTypes.value.find((item) => item.id === id)?.name ?? 'Unbekannter Typ'
}
</script>

<template>
  <v-container class="master-data-container pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-column flex-md-row justify-space-between align-md-start ga-4 mb-5">
      <div>
        <h1>Stammdaten</h1>
        <p class="text-medium-emphasis mb-0">
          Wiederverwendbare Kategorien, Produktmodelle und Kennzeichnungen zentral verwalten.
        </p>
      </div>
      <v-switch
        v-model="showArchived"
        label="Archivierte anzeigen"
        color="primary"
        hide-details
        inset
      />
    </div>

    <v-alert type="info" variant="tonal" class="mb-4">
      <strong>Asset-Typ</strong> beschreibt die Kategorie und bestimmt das Code-Präfix.
      <strong> Produkt</strong> beschreibt Hersteller, Modell und Bild, das viele Assets teilen können.
      <strong> Asset</strong> ist das konkrete Exemplar mit Ort, Serien- und Inventarnummer.
    </v-alert>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>
    <v-alert v-if="success" type="success" variant="tonal" class="mb-4" closable @click:close="success = null">
      {{ success }}
    </v-alert>

    <v-card rounded="xl">
      <v-tabs v-model="tab" color="primary" grow>
        <v-tab value="asset-types" prepend-icon="mdi-shape-outline">Asset-Typen</v-tab>
        <v-tab value="products" prepend-icon="mdi-package-variant-closed">Produkte</v-tab>
        <v-tab value="labels" prepend-icon="mdi-tag-multiple-outline">Labels</v-tab>
      </v-tabs>
      <v-divider />

      <div class="d-flex flex-column flex-sm-row justify-space-between align-sm-center ga-3 pa-4">
        <div class="text-medium-emphasis">
          <template v-if="tab === 'asset-types'">{{ assetTypes.length }} Asset-Typen</template>
          <template v-else-if="tab === 'products'">{{ products.length }} Produkte</template>
          <template v-else>{{ labels.length }} Labels</template>
        </div>
        <div class="d-flex flex-column flex-sm-row ga-2">
          <v-btn
            v-if="tab === 'asset-types'"
            variant="tonal"
            prepend-icon="mdi-auto-fix"
            :loading="importing"
            @click="addRecommendedAssetTypes"
          >
            Empfohlene Typen anlegen
          </v-btn>
          <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate(tab)">
            Neu anlegen
          </v-btn>
        </div>
      </div>

      <v-progress-linear v-if="loading" indeterminate color="primary" />

      <v-window v-else v-model="tab">
        <v-window-item value="asset-types">
          <v-alert v-if="assetTypes.length === 0" type="info" variant="tonal" class="ma-4">
            Noch keine Asset-Typen vorhanden. Lege einen Typ an oder übernimm die empfohlenen Typen.
          </v-alert>
          <div v-else class="table-scroll">
            <v-table hover>
              <thead><tr><th>Name</th><th>Code-Präfix</th><th>DIN</th><th>Beschreibung</th><th>Status</th><th class="text-right">Aktionen</th></tr></thead>
              <tbody>
                <tr v-for="item in assetTypes" :key="item.id">
                  <td>
                    <div class="d-flex align-center ga-2 font-weight-medium">
                      <v-icon :icon="item.icon || 'mdi-shape-outline'" size="20" />{{ item.name }}
                    </div>
                  </td>
                  <td><v-chip size="small" variant="tonal">{{ item.code_prefix }}</v-chip></td>
                  <td>{{ item.module_width ? `${item.module_width} TE` : '—' }}</td>
                  <td>{{ item.description || '—' }}</td>
                  <td><v-chip size="small" :color="item.deleted_at ? 'default' : 'success'" variant="tonal">{{ item.deleted_at ? 'Archiviert' : 'Aktiv' }}</v-chip></td>
                  <td class="text-right text-no-wrap">
                    <v-btn icon="mdi-pencil" variant="text" size="small" :disabled="Boolean(item.deleted_at)" :aria-label="`${item.name} bearbeiten`" :title="`${item.name} bearbeiten`" @click="editAssetType(item)" />
                    <v-btn icon="mdi-archive-outline" variant="text" size="small" color="warning" :disabled="Boolean(item.deleted_at)" :aria-label="`${item.name} archivieren`" :title="`${item.name} archivieren`" @click="askArchive('asset-types', item.id, item.name)" />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-window-item>

        <v-window-item value="products">
          <v-alert v-if="products.length === 0" type="info" variant="tonal" class="ma-4">
            Noch keine Produkte vorhanden. Produkte bündeln Hersteller, Modell und ein gemeinsames Bild.
          </v-alert>
          <div v-else class="table-scroll">
            <v-table hover>
              <thead><tr><th>Bild</th><th>Name</th><th>Hersteller</th><th>Modell</th><th>Asset-Typ</th><th>Status</th><th class="text-right">Aktionen</th></tr></thead>
              <tbody>
                <tr v-for="item in products" :key="item.id">
                  <td>
                    <v-avatar rounded="lg" size="52" color="surface-variant">
                      <v-img v-if="item.image_url" :src="item.image_url" :alt="`Produktbild ${item.name}`" cover />
                      <v-icon v-else icon="mdi-image-off-outline" />
                    </v-avatar>
                  </td>
                  <td class="font-weight-medium">{{ item.name }}</td>
                  <td>{{ item.manufacturer || '—' }}</td>
                  <td>{{ item.model_number || '—' }}</td>
                  <td>{{ assetTypeName(item.asset_type_id) }}</td>
                  <td><v-chip size="small" :color="item.deleted_at ? 'default' : 'success'" variant="tonal">{{ item.deleted_at ? 'Archiviert' : 'Aktiv' }}</v-chip></td>
                  <td class="text-right text-no-wrap">
                    <v-btn icon="mdi-pencil" variant="text" size="small" :disabled="Boolean(item.deleted_at)" :aria-label="`${item.name} bearbeiten`" :title="`${item.name} bearbeiten`" @click="editProduct(item)" />
                    <v-btn icon="mdi-archive-outline" variant="text" size="small" color="warning" :disabled="Boolean(item.deleted_at)" :aria-label="`${item.name} archivieren`" :title="`${item.name} archivieren`" @click="askArchive('products', item.id, item.name)" />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-window-item>

        <v-window-item value="labels">
          <v-alert v-if="labels.length === 0" type="info" variant="tonal" class="ma-4">
            Noch keine Labels vorhanden. Labels erleichtern spätere Filter und Auswertungen.
          </v-alert>
          <div v-else class="table-scroll">
            <v-table hover>
              <thead><tr><th>Name</th><th>Farbe</th><th>Status</th><th class="text-right">Aktionen</th></tr></thead>
              <tbody>
                <tr v-for="item in labels" :key="item.id">
                  <td class="font-weight-medium">{{ item.name }}</td>
                  <td><v-chip size="small" variant="outlined" :style="{ borderColor: item.color }"><span class="color-dot" :style="{ backgroundColor: item.color }" />{{ item.color }}</v-chip></td>
                  <td><v-chip size="small" :color="item.deleted_at ? 'default' : 'success'" variant="tonal">{{ item.deleted_at ? 'Archiviert' : 'Aktiv' }}</v-chip></td>
                  <td class="text-right text-no-wrap">
                    <v-btn icon="mdi-pencil" variant="text" size="small" :disabled="Boolean(item.deleted_at)" :aria-label="`${item.name} bearbeiten`" :title="`${item.name} bearbeiten`" @click="editLabel(item)" />
                    <v-btn icon="mdi-archive-outline" variant="text" size="small" color="warning" :disabled="Boolean(item.deleted_at)" :aria-label="`${item.name} archivieren`" :title="`${item.name} archivieren`" @click="askArchive('labels', item.id, item.name)" />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-window-item>
      </v-window>
    </v-card>

    <v-dialog v-model="editorOpen" max-width="760" persistent>
      <v-card :title="editorTitle">
        <v-form ref="formElement" @submit.prevent="saveEditor">
          <v-card-text>
            <template v-if="editorKind === 'asset-types'">
              <v-text-field
                v-model="assetTypeForm.name"
                label="Name"
                :rules="[requiredRule]"
                maxlength="100"
                hint="Kategorie mehrerer Geräte, zum Beispiel Sicherungsautomat oder Netzwerkgerät."
                persistent-hint
                autofocus
              />
              <AssetTypeIconPicker v-model="assetTypeForm.icon" class="mt-3" />
              <v-text-field
                v-model.number="assetTypeForm.module_width"
                label="Standard-DIN-Breite (optional)"
                type="number"
                min="1"
                max="100"
                suffix="TE"
                clearable
                hint="Assets dieses Typs sind ohne Produkt auf der Hutschiene platzierbar. Am einzelnen Asset kann die Breite überschrieben werden."
                persistent-hint
                class="mt-3"
              />
              <v-textarea
                v-model="assetTypeForm.description"
                label="Beschreibung (optional)"
                rows="3"
                auto-grow
                hint="Beschreibe, welche Geräte zu diesem Typ gehören."
                persistent-hint
              />
              <v-alert type="info" variant="tonal" density="compact">
                Das technische Code-Präfix wird beim Anlegen automatisch vergeben und bleibt für bestehende Assets stabil.
              </v-alert>
            </template>
            <template v-else-if="editorKind === 'products'">
              <v-text-field
                v-model="productForm.name"
                label="Produktname"
                :rules="[requiredRule]"
                maxlength="150"
                hint="Wiederverwendbares Modell, nicht das einzelne physische Gerät."
                persistent-hint
                autofocus
              />
              <v-row class="mt-1">
                <v-col cols="12" sm="6">
                  <v-text-field v-model="productForm.manufacturer" label="Hersteller (optional)" maxlength="150" hint="Zum Beispiel ABB, Hager oder Shelly." persistent-hint />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field v-model="productForm.model_number" label="Modellnummer (optional)" maxlength="150" hint="Herstellerbezeichnung oder Artikelnummer." persistent-hint />
                </v-col>
              </v-row>
              <v-select
                v-model="productForm.asset_type_id"
                label="Asset-Typ (optional)"
                :items="activeAssetTypes"
                item-title="name"
                item-value="id"
                hint="Begrenzt das Produkt auf passende Assets dieses Typs."
                persistent-hint
                clearable
              />
              <ProductImageField
                v-model="productForm.image_url"
                v-model:source="productForm.image_source"
                v-model:reference="productForm.image_reference"
                :search-terms="[productForm.manufacturer, productForm.name, productForm.model_number].filter(Boolean).join(' ')"
                class="mt-3"
              />
              <v-switch
                v-model="productForm.din_rail_mount"
                label="Bauform DIN-Hutschiene"
                color="primary"
                inset
                hide-details
                class="mt-4"
                @update:model-value="!$event && (productForm.module_width = null)"
              />
              <v-text-field
                v-if="productForm.din_rail_mount"
                v-model.number="productForm.module_width"
                label="Breite in Teilungseinheiten (TE)"
                type="number"
                min="1"
                max="100"
                suffix="TE"
                hint="Wird bei der Platzierung im Zählerschrank als Standardbreite verwendet."
                persistent-hint
              />
              <v-textarea
                v-model="productForm.description"
                label="Beschreibung (optional)"
                rows="3"
                auto-grow
                hint="Technische Besonderheiten, Ausführung oder Verwendungszweck."
                persistent-hint
              />
            </template>
            <template v-else>
              <v-text-field
                v-model="labelForm.name"
                label="Name"
                :rules="[requiredRule]"
                maxlength="100"
                hint="Freie Kennzeichnung wie Kritisch, Außenbereich oder Ersatzteil."
                persistent-hint
                autofocus
              />
              <v-text-field v-model="labelForm.color" label="Farbe" type="color" :rules="[colorRule]" />
            </template>
          </v-card-text>
          <v-card-actions class="pa-4 pt-0">
            <v-spacer />
            <v-btn variant="text" :disabled="saving" @click="editorOpen = false">Abbrechen</v-btn>
            <v-btn type="submit" color="primary" prepend-icon="mdi-content-save" :loading="saving">Speichern</v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>

    <v-dialog :model-value="Boolean(archiveTarget)" max-width="520" @update:model-value="(value) => { if (!value) archiveTarget = null }">
      <v-card title="Stammdatum archivieren" prepend-icon="mdi-archive-outline">
        <v-card-text>
          <strong>{{ archiveTarget?.name }}</strong> wird archiviert und steht für neue Zuordnungen nicht mehr zur Verfügung.
          Historische Verknüpfungen bleiben erhalten.
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" :disabled="saving" @click="archiveTarget = null">Abbrechen</v-btn>
          <v-btn color="warning" prepend-icon="mdi-archive" :loading="saving" @click="confirmArchive">Archivieren</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.master-data-container { max-width: 1250px; }
h1 { font-size: clamp(1.8rem, 4vw, 2.25rem); }
.table-scroll { overflow-x: auto; }
th { white-space: nowrap; }
.color-dot { width: 0.75rem; height: 0.75rem; margin-right: 0.4rem; border-radius: 50%; display: inline-block; }
</style>
