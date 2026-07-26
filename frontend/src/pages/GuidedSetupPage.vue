<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { assetApi } from '../services/assetApi'
import { releaseApi } from '../services/releaseApi'
import { immichApi } from '../services/immichApi'
import { settingsApi } from '../services/settingsApi'
import type { ImmichImage } from '../types/immich'
import type { Asset, AssetType } from '../types/assets'
import type {
  GuidedSetupApply,
  GuidedSetupDraft,
  GuidedSetupPreview
} from '../types/release'

const router = useRouter()
const step = ref(1)
const draftId = ref<string | null>(null)
const draftName = ref('Neue Hauskomponente')
const assetMode = ref<'new' | 'existing'>('new')
const existingAssetId = ref<string | null>(null)
const existingAssets = ref<Asset[]>([])
const assetTypes = ref<AssetType[]>([])
const asset = ref({
  name: '',
  asset_type_id: '',
  product_id: null as string | null,
  location_id: null as string | null,
  description: null as string | null,
  serial_number: null as string | null,
  inventory_number: null as string | null,
  status: 'active',
  label_ids: [] as string[]
})
const networkEnabled = ref(false)
const network = ref({ role: 'other', hostname: '', management_url: '', notes: '' })
const consumptionEnabled = ref(false)
const consumption = ref({
  name: '',
  meter_type: 'water',
  unit: 'm³',
  decimals: 3,
  sort_order: 100,
  serial_number: null,
  location_id: null,
  parent_meter_id: null,
  home_assistant_entity_id: null,
  water_role: 'none',
  primary_for_dashboard: false,
  reading_schedule_day: null as number | null,
  reading_schedule_last_day: false,
  reminder_days: [] as number[],
  notes: null
})
const electricalCircuitId = ref('')
const homeAssistantDeviceIds = ref('')
const documentPath = ref('')
const imageId = ref('')
const imageName = ref('')
const immichImages = ref<ImmichImage[]>([])
const immichLoading = ref(false)
const immichAlbumId = ref<string | null>(null)
const immichSearch = ref('')
const maintenanceTitle = ref('')
const maintenanceDue = ref('')
const note = ref('')
const preview = ref<GuidedSetupPreview | null>(null)
const applied = ref<GuidedSetupApply | null>(null)
const error = ref<string | null>(null)
const saving = ref(false)

const stepItems = [
  'Umfang',
  'Bestehendes Objekt',
  'Asset, Typ & Ort',
  'Elektrische Zuleitung',
  'Leiter & Kabel',
  'Schutzgerät & Stromkreis',
  'Netzwerk & Verbrauch',
  'Bilder & Dokumente',
  'Offene Komponenten',
  'Vorschau',
  'Speichern'
]
const selectedExistingAsset = computed(() => existingAssets.value.find((item) => item.id === existingAssetId.value) ?? null)
const existingAssetItems = computed(() => existingAssets.value.map((item) => ({
  value: item.id,
  title: item.name,
  subtitle: [item.jarvis_code, item.asset_type.name, item.location?.name, item.inventory_number].filter(Boolean).join(' · ')
})))
const canContinue = computed(() => {
  if (step.value === 1) return Boolean(draftName.value.trim())
  if (step.value === 2) return assetMode.value === 'new' || Boolean(existingAssetId.value)
  if (step.value === 3 && assetMode.value === 'new') {
    return Boolean(asset.value.name.trim() && asset.value.asset_type_id)
  }
  return step.value < 10 || Boolean(preview.value?.can_apply)
})

function payload() {
  const data: Record<string, unknown> = {}
  if (assetMode.value === 'existing' && existingAssetId.value) data.existing_asset_id = existingAssetId.value
  else data.asset = asset.value
  if (networkEnabled.value) data.network = network.value
  if (consumptionEnabled.value) data.consumption = consumption.value
  if (electricalCircuitId.value) data.electrical = { circuit_id: electricalCircuitId.value }
  if (homeAssistantDeviceIds.value.trim()) {
    data.home_assistant = {
      device_ids: homeAssistantDeviceIds.value.split(',').map((item) => item.trim()).filter(Boolean)
    }
  }
  if (documentPath.value.trim()) {
    data.documents = [{ path: documentPath.value.trim(), name: documentPath.value.split('/').pop() }]
  }
  if (imageId.value.trim() && imageName.value.trim()) {
    data.images = [{ id: imageId.value.trim(), name: imageName.value.trim() }]
  }
  if (maintenanceTitle.value.trim()) {
    data.maintenance = {
      title: maintenanceTitle.value.trim(),
      due_at: maintenanceDue.value ? new Date(maintenanceDue.value).toISOString() : null
    }
  }
  if (note.value.trim()) data.note = note.value.trim()
  return { name: draftName.value, current_step: step.value, data }
}

async function loadImmichImages() {
  if (!immichAlbumId.value) return
  immichLoading.value = true
  try {
    const result = await immichApi.browse({
      album_id: immichAlbumId.value, page: 1, page_size: 50,
      search: immichSearch.value || undefined
    })
    immichImages.value = result.items
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Immich-Bilder konnten nicht geladen werden.'
  } finally {
    immichLoading.value = false
  }
}

function selectImmichImage(image: ImmichImage) {
  imageId.value = image.immich_asset_id
  imageName.value = image.original_file_name
}

async function saveDraft() {
  saving.value = true
  error.value = null
  try {
    const record: GuidedSetupDraft = draftId.value
      ? await releaseApi.updateDraft(draftId.value, payload())
      : await releaseApi.createDraft(payload())
    draftId.value = record.id
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Entwurf konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function createPreview() {
  await saveDraft()
  if (!draftId.value) return
  preview.value = await releaseApi.previewDraft(draftId.value)
  step.value = 10
}

async function applyDraft() {
  if (!draftId.value || !preview.value?.can_apply) return
  saving.value = true
  try {
    applied.value = await releaseApi.applyDraft(draftId.value)
    step.value = 11
    window.setTimeout(() => void router.replace({ name: 'guided-setup' }), 1400)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Assistent konnte nicht speichern.'
  } finally {
    saving.value = false
  }
}

watch(assetMode, (mode) => {
  if (mode === 'new') existingAssetId.value = null
})

async function next() {
  await saveDraft()
  if (step.value < 9) step.value += 1
  else await createPreview()
}

onMounted(async () => {
  const [typePage, assetRows] = await Promise.all([assetApi.assetTypes(), assetApi.allAssets()])
  assetTypes.value = typePage.items
  existingAssets.value = assetRows
  try {
    const configuration = await settingsApi.read()
    immichAlbumId.value = configuration.integrations.find((item) => item.kind === 'immich')?.selected_album_id ?? null
    if (immichAlbumId.value) await loadImmichImages()
  } catch {
    // The assistant remains usable without Immich.
  }
})
</script>

<template>
  <v-container fluid class="pa-4 pa-md-6">
    <h1 class="text-h4 font-weight-bold">Geführte Einrichtung</h1>
    <p class="text-medium-emphasis mb-4">
      Bestehende Objekte bevorzugen, keine technischen Werte erraten und alles erst nach Vorschau
      in einer Transaktion speichern.
    </p>
    <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>
    <v-progress-linear :model-value="step / 11 * 100" class="mb-4" />

    <v-card>
      <v-card-title>Schritt {{ step }} von 11 · {{ stepItems[step - 1] }}</v-card-title>
      <v-card-text>
        <v-window v-model="step">
          <v-window-item :value="1">
            <v-text-field v-model="draftName" label="Name des Entwurfs" />
            <v-alert type="info" variant="tonal">
              Wähle nur die Module aus, die für diese Hauskomponente tatsächlich relevant sind.
            </v-alert>
            <v-checkbox v-model="networkEnabled" label="Netzwerk dokumentieren" />
            <v-checkbox v-model="consumptionEnabled" label="Verbrauchszähler dokumentieren" />
          </v-window-item>
          <v-window-item :value="2">
            <v-radio-group v-model="assetMode" label="Wie möchtest du fortfahren?" class="mb-3">
              <v-radio value="new" label="Neues Objekt anlegen" />
              <v-radio value="existing" label="Bestehendes Objekt ergänzen" />
            </v-radio-group>
            <v-autocomplete
              v-if="assetMode === 'existing'"
              v-model="existingAssetId"
              :items="existingAssetItems"
              item-title="title"
              item-value="value"
              label="Vorhandenes Asset auswählen"
              placeholder="Name, DocOfHome-Code, Typ, Raum oder Inventarnummer suchen"
              prepend-inner-icon="mdi-magnify"
              clearable
              auto-select-first
              no-data-text="Kein passendes Asset gefunden"
              hint="Die technischen Stammdaten werden nicht überschrieben. Der Assistent ergänzt nur ausgewählte Verknüpfungen und Module."
              persistent-hint
            >
              <template #item="{ props, item }">
                <v-list-item v-bind="props" :title="item.raw.title" :subtitle="item.raw.subtitle" />
              </template>
            </v-autocomplete>
            <v-alert v-else type="info" variant="tonal">
              In Schritt 3 erfasst du Name, Typ und Ort für ein neues Asset.
            </v-alert>
            <v-card v-if="assetMode === 'existing' && selectedExistingAsset" variant="tonal" class="mt-4">
              <v-card-title>{{ selectedExistingAsset.name }}</v-card-title>
              <v-card-text>
                {{ selectedExistingAsset.jarvis_code }} · {{ selectedExistingAsset.asset_type.name }}
                <span v-if="selectedExistingAsset.location"> · {{ selectedExistingAsset.location.name }}</span>
              </v-card-text>
              <v-card-actions>
                <v-btn variant="text" prepend-icon="mdi-pencil" :to="`/assets/${selectedExistingAsset.id}/edit`">
                  Stammdaten bearbeiten
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-window-item>
          <v-window-item :value="3">
            <template v-if="assetMode === 'new'">
              <v-text-field v-model="asset.name" label="Asset-Name" />
              <v-select
                v-model="asset.asset_type_id"
                :items="assetTypes"
                item-title="name"
                item-value="id"
                label="Asset-Typ"
              />
              <v-textarea v-model="asset.description" label="Beschreibung" />
            </template>
            <v-alert v-else type="info" variant="tonal">
              Das ausgewählte Asset wird wiederverwendet. Name, Typ, Beschreibung und Raum bleiben unverändert.
              Nutze „Stammdaten bearbeiten“ in Schritt 2, wenn du diese Angaben ändern möchtest.
            </v-alert>
          </v-window-item>
          <v-window-item :value="4">
            <v-alert type="info" variant="tonal">
              Eine elektrische Zuleitung wird nur über einen vorhandenen, ausdrücklich gewählten
              Stromkreis zugeordnet. DocOfHome errät keine Verdrahtung.
            </v-alert>
          </v-window-item>
          <v-window-item :value="5">
            <v-alert type="warning" variant="tonal">
              Phase, Leiter, Kabeltyp und Querschnitt müssen an bestehenden Elektroobjekten gepflegt
              sein. Fehlende Angaben können in Schritt 9 als offene Notiz festgehalten werden.
            </v-alert>
          </v-window-item>
          <v-window-item :value="6">
            <v-text-field v-model="electricalCircuitId" label="Vorhandene Stromkreis-ID (optional)" />
          </v-window-item>
          <v-window-item :value="7">
            <template v-if="networkEnabled">
              <v-select
                v-model="network.role"
                label="Netzwerkrolle"
                :items="['router', 'firewall', 'switch', 'access_point', 'server', 'nas', 'client', 'iot', 'printer', 'controller', 'other']"
              />
              <v-text-field v-model="network.hostname" label="Hostname (optional)" />
            </template>
            <template v-if="consumptionEnabled">
              <v-text-field v-model="consumption.name" label="Zählername" />
              <v-select
                v-model="consumption.meter_type"
                label="Medium"
                :items="['water', 'electricity_grid', 'electricity_pv', 'electricity_feed_in', 'gas', 'heat', 'oil', 'other']"
              />
              <v-text-field v-model="consumption.unit" label="Einheit" />
            </template>
            <v-text-field
              v-model="homeAssistantDeviceIds"
              label="Home-Assistant-Geräte-IDs (kommagetrennt, optional)"
            />
          </v-window-item>
          <v-window-item :value="8">
            <v-text-field v-model="documentPath" label="Nextcloud-Dokumentpfad (optional)" />
            <v-alert v-if="!immichAlbumId" type="info" variant="tonal" class="mb-3">
              Wähle zuerst in den Einstellungen ein Immich-Album aus. Danach kannst du hier Bilder visuell auswählen.
            </v-alert>
            <template v-else>
              <div class="d-flex ga-2 mb-3">
                <v-text-field v-model="immichSearch" label="Bild im festgelegten Immich-Album suchen"
                  prepend-inner-icon="mdi-magnify" hide-details @keyup.enter="loadImmichImages" />
                <v-btn variant="tonal" prepend-icon="mdi-refresh" :loading="immichLoading" @click="loadImmichImages">Laden</v-btn>
              </div>
              <v-row>
                <v-col v-for="image in immichImages" :key="image.immich_asset_id" cols="6" md="3">
                  <v-card variant="outlined" :color="imageId === image.immich_asset_id ? 'primary' : undefined"
                    @click="selectImmichImage(image)">
                    <v-img :src="image.thumbnail_url" aspect-ratio="1" cover />
                    <v-card-text class="text-caption text-truncate">{{ image.original_file_name }}</v-card-text>
                  </v-card>
                </v-col>
              </v-row>
              <v-alert v-if="imageId" type="success" variant="tonal" density="compact" class="mt-3">
                Ausgewählt: {{ imageName }}
              </v-alert>
            </template>
          </v-window-item>
          <v-window-item :value="9">
            <v-textarea
              v-model="note"
              label="Offene Komponenten oder fehlende technische Angaben"
              rows="4"
            />
            <v-text-field v-model="maintenanceTitle" label="Wartungstitel (optional)" />
            <v-text-field v-model="maintenanceDue" type="datetime-local" label="Fälligkeit" />
          </v-window-item>
          <v-window-item :value="10">
            <v-list v-if="preview">
              <v-list-item
                v-for="action in preview.actions"
                :key="action"
                prepend-icon="mdi-check-circle-outline"
                :title="action"
              />
            </v-list>
            <v-alert v-for="item in preview?.warnings ?? []" :key="item" type="warning" class="mb-2">
              {{ item }}
            </v-alert>
            <v-alert v-for="item in preview?.errors ?? []" :key="item" type="error" class="mb-2">
              {{ item }}
            </v-alert>
          </v-window-item>
          <v-window-item :value="11">
            <v-alert v-if="applied" type="success">
              Einrichtung vollständig gespeichert. Asset-ID: {{ applied.asset_id }}. Du wirst zum Anfang zurückgeführt.
            </v-alert>
          </v-window-item>
        </v-window>
      </v-card-text>
      <v-card-actions>
        <v-btn :disabled="step <= 1 || step === 11" @click="step -= 1">Zurück</v-btn>
        <v-spacer />
        <v-btn variant="text" :loading="saving" @click="saveDraft">Entwurf speichern</v-btn>
        <v-btn
          v-if="step < 10"
          color="primary"
          :disabled="!canContinue"
          :loading="saving"
          @click="next"
        >
          Weiter
        </v-btn>
        <v-btn
          v-else-if="step === 10"
          color="primary"
          :disabled="!preview?.can_apply"
          :loading="saving"
          @click="applyDraft"
        >
          Transaktional speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-container>
</template>
