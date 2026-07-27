<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { assetApi } from '../services/assetApi'
import { locationApi } from '../services/locationApi'
import { flattenLocationTree } from '../services/locationOptions'
import { isSafeLocalRoute } from '../services/searchApi'
import {
  createEmptyAsset,
  editableAsset,
  type AssetType,
  type Label,
  type Location,
  type Product
} from '../types/assets'

type FormHandle = { validate: () => Promise<{ valid: boolean }> }

const route = useRoute()
const router = useRouter()
const formElement = ref<FormHandle | null>(null)
const form = ref(createEmptyAsset())
const assetTypes = ref<AssetType[]>([])
const products = ref<Product[]>([])
const locations = ref<Location[]>([])
const labels = ref<Label[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const existingCode = ref<string | null>(null)
const replacementReason = ref('')
const labelDialog = ref(false)
const labelSaving = ref(false)
const labelForm = ref({ name: '', color: '#26c6da' })
const assetId = computed(() => route.params.id ? String(route.params.id) : null)
const isReplacing = computed(() => route.name === 'asset-replace')
const isEditing = computed(() => assetId.value !== null && !isReplacing.value)
const returnTo = computed(() => {
  const value = typeof route.query.return_to === 'string' ? route.query.return_to : null
  return value && isSafeLocalRoute(value) ? value : null
})
const title = computed(() => {
  if (isReplacing.value) return 'Asset ersetzen'
  return isEditing.value ? 'Asset bearbeiten' : 'Asset erfassen'
})
const matchingProducts = computed(() => products.value.filter(
  (product) => !product.asset_type_id || product.asset_type_id === form.value.asset_type_id
))
const selectedProduct = computed(() => products.value.find(
  (product) => product.id === form.value.product_id
) ?? null)
const selectedAssetType = computed(() => assetTypes.value.find(
  (assetType) => assetType.id === form.value.asset_type_id
) ?? null)
const inheritedModuleWidth = computed(() => (
  selectedProduct.value?.din_rail_mount && selectedProduct.value.module_width
    ? selectedProduct.value.module_width
    : selectedAssetType.value?.module_width ?? null
))
const selectedAssetTypeName = computed(() => (
  selectedAssetType.value?.name.trim().toLocaleLowerCase('de') ?? ''
))
const isBreakerAsset = computed(() => (
  selectedAssetTypeName.value.includes('sicherungsautomat')
  || selectedAssetTypeName.value.includes('leitungsschutz')
))
const isImpulseSwitchAsset = computed(() => (
  selectedAssetTypeName.value.includes('stromstoß')
  || selectedAssetTypeName.value.includes('stromstoss')
))
const inheritedBreakerCharacteristic = computed(() => selectedAssetType.value?.breaker_characteristic ?? null)
const inheritedRatedCurrent = computed(() => selectedAssetType.value?.rated_current_a ?? null)
const inheritedCoilVoltage = computed(() => selectedAssetType.value?.coil_voltage_v ?? null)
const inheritedCoilVoltageType = computed(() => selectedAssetType.value?.coil_voltage_type ?? null)
const inheritedContactCount = computed(() => selectedAssetType.value?.contact_count ?? null)
const inheritedContactType = computed(() => selectedAssetType.value?.contact_type ?? null)
const contactTypeItems = [
  { title: 'Schließer', value: 'normally_open' },
  { title: 'Öffner', value: 'normally_closed' },
  { title: 'Wechsler', value: 'changeover' }
]

const requiredRule = (value: string | null) => Boolean(value?.trim()) || 'Dieses Feld ist erforderlich.'
const statusItems = [
  { title: 'Aktiv', value: 'active' },
  { title: 'Inaktiv', value: 'inactive' },
  { title: 'Wartung', value: 'maintenance' },
  { title: 'Ausgemustert', value: 'retired' }
]

onMounted(async () => {
  try {
    const [types, productPage, locationPage, labelPage] = await Promise.all([
      assetApi.assetTypes(), assetApi.products(), locationApi.tree(), assetApi.labels()
    ])
    assetTypes.value = types.items
    products.value = productPage.items
    locations.value = flattenLocationTree(locationPage)
    labels.value = labelPage.items
    if (!assetId.value) {
      if (typeof route.query.name === 'string') form.value.name = route.query.name.slice(0, 150)
      if (typeof route.query.description === 'string') form.value.description = route.query.description.slice(0, 1000)
    }
    if (assetId.value) {
      const asset = await assetApi.get(assetId.value)
      existingCode.value = asset.jarvis_code
      form.value = editableAsset(asset)
      if (isReplacing.value) form.value.status = 'active'
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Asseteditor konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
})

async function suggestInventoryNumber() {
  try {
    form.value.inventory_number = await assetApi.nextInventoryNumber()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Inventarnummer konnte nicht ermittelt werden.'
  }
}

async function createInlineLabel() {
  const name = labelForm.value.name.trim()
  if (!name) return
  const duplicate = labels.value.find((label) => label.name.trim().toLocaleLowerCase() === name.toLocaleLowerCase())
  if (duplicate) {
    if (!form.value.label_ids.includes(duplicate.id)) form.value.label_ids.push(duplicate.id)
    error.value = `Das Label „${duplicate.name}“ existiert bereits und wurde ausgewählt.`
    labelDialog.value = false
    return
  }
  labelSaving.value = true
  error.value = null
  try {
    const created = await assetApi.createLabel({ name, color: labelForm.value.color })
    labels.value = [...labels.value, created].sort((a, b) => a.name.localeCompare(b.name, 'de'))
    form.value.label_ids = [...new Set([...form.value.label_ids, created.id])]
    labelForm.value = { name: '', color: '#26c6da' }
    labelDialog.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Label konnte nicht angelegt werden.'
  } finally {
    labelSaving.value = false
  }
}

async function save() {
  const validation = await formElement.value?.validate()
  if (validation && !validation.valid) return
  saving.value = true
  error.value = null
  try {
    let saved
    if (assetId.value && isReplacing.value) {
      const result = await assetApi.replace(assetId.value, form.value, replacementReason.value)
      saved = result.replacement
    } else if (assetId.value) {
      saved = await assetApi.update(assetId.value, form.value)
    } else {
      saved = await assetApi.create(form.value)
    }
    await router.push(returnTo.value ?? `/assets/${saved.id}`)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Asset konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-container class="asset-editor pa-4 pa-sm-6" fluid>
    <v-btn variant="text" prepend-icon="mdi-arrow-left" :to="assetId ? `/assets/${assetId}` : '/assets'" class="mb-3">
      {{ assetId ? 'Zur Detailansicht' : 'Zur Assetliste' }}
    </v-btn>
    <div class="mb-5">
      <h1>{{ title }}</h1>
      <p class="text-medium-emphasis">Das konkrete physische Gerät mit Ort und eindeutigen Kennungen dokumentieren.</p>
    </div>
    <v-skeleton-loader v-if="loading" type="heading, card, card" />
    <v-form v-else ref="formElement" @submit.prevent="save">
      <v-alert v-if="error" type="error" variant="tonal" class="mb-5">{{ error }}</v-alert>
      <v-alert type="info" variant="tonal" class="mb-5">
        <strong>Asset-Typ</strong> ist die Kategorie, <strong>Produkt</strong> das Hersteller-Modell
        und dieses <strong>Asset</strong> das einzelne Gerät mit eigener Serien- und Inventarnummer.
      </v-alert>
      <v-alert v-if="isReplacing" type="info" variant="tonal" class="mb-5">
        Das bisherige Asset {{ existingCode }} wird unveränderlich als ausgemustert archiviert.
        Das Ersatzobjekt erhält automatisch einen neuen DocOfHome-Code und eine feste
        <code>replaced_by</code>-Beziehung.
      </v-alert>
      <v-alert v-if="assetTypes.length === 0" type="warning" variant="tonal" class="mb-5">
        <div class="d-flex flex-column flex-sm-row align-sm-center justify-space-between ga-3">
          <span>Vor dem ersten Asset muss mindestens ein Asset-Typ angelegt werden.</span>
          <v-btn variant="tonal" color="primary" prepend-icon="mdi-database-cog-outline" to="/master-data?tab=asset-types">
            Stammdaten öffnen
          </v-btn>
        </div>
      </v-alert>

      <v-card title="Allgemein" prepend-icon="mdi-package-variant" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col v-if="isEditing" cols="12" md="4">
              <v-text-field :model-value="existingCode" label="DocOfHome-Code" prepend-inner-icon="mdi-identifier" readonly disabled hint="Automatisch vergeben und unveränderlich" persistent-hint />
            </v-col>
            <v-col cols="12" :md="isEditing ? 5 : 8">
              <v-text-field v-model="form.name" label="Name" :rules="[requiredRule]" maxlength="150" hint="Erkennbarer Name des konkreten Geräts, zum Beispiel LS Küche Licht." persistent-hint autofocus />
            </v-col>
            <v-col cols="12" md="4">
              <v-select v-model="form.status" label="Status" :items="statusItems" hint="Lebenszyklus des konkreten Geräts." persistent-hint />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="form.description" label="Beschreibung" rows="3" auto-grow hint="Aufgabe, versorgter Bereich oder Besonderheiten dieses Geräts." persistent-hint />
            </v-col>
            <v-col v-if="isReplacing" cols="12">
              <v-textarea v-model="replacementReason" label="Grund für den Ersatz (optional)" rows="2" maxlength="1000" />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card title="Klassifikation und Ort" prepend-icon="mdi-shape-outline" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="4">
              <v-select v-model="form.asset_type_id" label="Asset-Typ" :items="assetTypes" item-title="name" item-value="id" :rules="[requiredRule]" hint="Kategorie und Basis des automatischen DocOfHome-Codes." persistent-hint>
                <template #item="{ props, item }"><v-list-item v-bind="props" :prepend-icon="item.raw.icon || 'mdi-shape-outline'" /></template>
              </v-select>
            </v-col>
            <v-col cols="12" md="4">
              <v-select v-model="form.product_id" label="Produkt (optional)" :items="matchingProducts" item-title="name" item-value="id" hint="Hersteller-Modell, das auch das Produktbild liefert." persistent-hint clearable />
            </v-col>
            <v-col cols="12" md="4">
              <v-select v-model="form.location_id" label="Ort (optional)" :items="locations" item-title="path" item-value="id" hint="Physischer Einbau- oder Aufbewahrungsort." persistent-hint clearable />
            </v-col>
            <v-col cols="12" md="4">
              <v-text-field
                v-model.number="form.module_width"
                label="DIN-Breite (optional)"
                type="number"
                min="1"
                max="100"
                suffix="TE"
                clearable
                :hint="inheritedModuleWidth
                  ? `Leer lassen, um ${inheritedModuleWidth} TE aus Produkt oder Asset-Typ zu übernehmen.`
                  : 'Erst mit einer DIN-Breite kann dieses Asset auf einer Hutschiene platziert werden.'"
                persistent-hint
              />
            </v-col>
            <template v-if="isBreakerAsset">
              <v-col cols="12" md="4">
                <v-select
                  v-model="form.breaker_characteristic"
                  :items="['B', 'C', 'D', 'K', 'Z']"
                  label="Auslösecharakteristik (optional)"
                  clearable
                  :hint="inheritedBreakerCharacteristic
                    ? `Leer lassen, um ${inheritedBreakerCharacteristic} aus dem Asset-Typ zu übernehmen.`
                    : 'Zum Beispiel B oder C.'"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-text-field
                  v-model.number="form.rated_current_a"
                  label="Nennstrom (optional)"
                  type="number"
                  min="0.1"
                  max="10000"
                  step="0.1"
                  suffix="A"
                  clearable
                  :hint="inheritedRatedCurrent
                    ? `Leer lassen, um ${inheritedRatedCurrent} A aus dem Asset-Typ zu übernehmen.`
                    : 'Zum Beispiel 16 A.'"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="4" class="d-flex align-center">
                <v-chip v-if="form.breaker_characteristic || inheritedBreakerCharacteristic" color="primary" variant="tonal">
                  Technische Kurzbezeichnung:
                  {{ form.breaker_characteristic || inheritedBreakerCharacteristic }}{{ form.rated_current_a || inheritedRatedCurrent || '?' }}
                </v-chip>
              </v-col>
            </template>
            <template v-if="isImpulseSwitchAsset">
              <v-col cols="12" md="3">
                <v-text-field
                  v-model.number="form.rated_current_a"
                  label="Kontakt-Nennstrom (optional)"
                  type="number"
                  min="0.1"
                  max="10000"
                  step="0.1"
                  suffix="A"
                  clearable
                  :hint="inheritedRatedCurrent ? `Standard: ${inheritedRatedCurrent} A` : 'Zum Beispiel 16 A.'"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="3">
                <v-text-field
                  v-model.number="form.coil_voltage_v"
                  label="Spulenspannung (optional)"
                  type="number"
                  min="0.1"
                  max="10000"
                  step="0.1"
                  suffix="V"
                  clearable
                  :hint="inheritedCoilVoltage ? `Standard: ${inheritedCoilVoltage} V` : 'Zum Beispiel 230 V.'"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="2">
                <v-select
                  v-model="form.coil_voltage_type"
                  :items="['AC', 'DC']"
                  label="Spannungsart"
                  clearable
                  :hint="inheritedCoilVoltageType ? `Standard: ${inheritedCoilVoltageType}` : undefined"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="2">
                <v-text-field
                  v-model.number="form.contact_count"
                  label="Kontaktanzahl"
                  type="number"
                  min="1"
                  max="100"
                  step="1"
                  clearable
                  :hint="inheritedContactCount ? `Standard: ${inheritedContactCount}` : undefined"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" md="2">
                <v-select
                  v-model="form.contact_type"
                  :items="contactTypeItems"
                  label="Kontaktart"
                  clearable
                  :hint="inheritedContactType ? 'Vom Asset-Typ vorbelegt' : undefined"
                  persistent-hint
                />
              </v-col>
            </template>
            <v-col v-if="selectedProduct" cols="12">
              <v-card variant="tonal" class="d-flex flex-column flex-sm-row align-center pa-3 ga-4">
                <v-avatar rounded="lg" size="120" color="surface-variant">
                  <v-img v-if="selectedProduct.image_url" :src="selectedProduct.image_url" :alt="`Produktbild ${selectedProduct.name}`" contain />
                  <v-icon v-else icon="mdi-image-off-outline" size="42" />
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-h6">{{ selectedProduct.name }}</div>
                  <div class="text-medium-emphasis">
                    {{ selectedProduct.manufacturer || 'Hersteller unbekannt' }}
                    <span v-if="selectedProduct.model_number"> · {{ selectedProduct.model_number }}</span>
                  </div>
                  <p class="mt-2 mb-0">{{ selectedProduct.description || 'Keine Produktbeschreibung hinterlegt.' }}</p>
                </div>
              </v-card>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <v-card title="Identifikation und Labels" prepend-icon="mdi-barcode-scan" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <div class="d-flex align-start ga-2">
                <v-text-field v-model="form.inventory_number" label="Inventarnummer" maxlength="200" hint="Interne Kennzeichnung; +1 erhöht die letzte Zahl inklusive führender Nullen." persistent-hint class="flex-grow-1" />
                <v-tooltip text="Nächste freie Inventarnummer serverseitig ermitteln">
                  <template #activator="{ props }">
                    <v-btn v-bind="props" icon="mdi-plus" color="primary" variant="tonal" class="mt-1" aria-label="Nächste freie Inventarnummer" title="Nächste freie Inventarnummer" @click="suggestInventoryNumber" />
                  </template>
                </v-tooltip>
              </div>
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field v-model="form.serial_number" label="Seriennummer" maxlength="200" hint="Vom Hersteller vergebene Nummer dieses einzelnen Geräts." persistent-hint />
            </v-col>
            <v-col cols="12">
              <div class="d-flex align-start ga-2">
                <v-select v-model="form.label_ids" label="Labels" :items="labels" item-title="name" item-value="id" multiple chips closable-chips clearable hint="Freie Kennzeichnungen für Filter und spätere Auswertungen." persistent-hint class="flex-grow-1">
                  <template #chip="{ props, item }"><v-chip v-bind="props" :style="{ borderColor: item.raw.color }" variant="outlined" /></template>
                </v-select>
                <v-btn
                  class="mt-1"
                  color="primary"
                  variant="tonal"
                  prepend-icon="mdi-tag-plus-outline"
                  @click="labelDialog = true"
                >Neues Label</v-btn>
              </div>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <div class="d-flex flex-column-reverse flex-sm-row justify-end ga-3">
        <v-btn variant="text" :to="assetId ? `/assets/${assetId}` : '/assets'">Abbrechen</v-btn>
        <v-btn type="submit" color="primary" prepend-icon="mdi-content-save" :loading="saving" :disabled="assetTypes.length === 0">
          {{ isReplacing ? 'Ersatz-Asset anlegen' : 'Asset speichern' }}
        </v-btn>
      </div>
    </v-form>

    <v-dialog v-model="labelDialog" max-width="520">
      <v-card title="Neues Label anlegen" prepend-icon="mdi-tag-plus-outline">
        <v-card-text>
          <v-text-field v-model="labelForm.name" label="Name" maxlength="100" autofocus />
          <v-text-field v-model="labelForm.color" label="Farbe" type="color" />
          <v-alert type="info" variant="tonal" density="compact">
            Das neue Label wird sofort gespeichert und diesem Asset direkt zugeordnet.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" :disabled="labelSaving" @click="labelDialog = false">Abbrechen</v-btn>
          <v-btn color="primary" :loading="labelSaving" :disabled="!labelForm.name.trim()" @click="createInlineLabel">Anlegen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.asset-editor { max-width: 1100px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.2rem); }
</style>
