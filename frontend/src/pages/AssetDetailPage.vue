<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { inventoryReturnTo } from '../services/inventoryNavigation'
import { useSettingsStore } from '../stores/settings'
import { moduleKeys } from '../types/settings'
import AssetDuplicateDialog from '../components/AssetDuplicateDialog.vue'
import DocumentLinksCard from '../components/DocumentLinksCard.vue'
import ConsumptionMetersCard from '../components/ConsumptionMetersCard.vue'
import HomeAssistantAssetCard from '../components/HomeAssistantAssetCard.vue'
import MaintenanceCard from '../components/MaintenanceCard.vue'
import NetworkAssetCard from '../components/NetworkAssetCard.vue'
import NotesCard from '../components/NotesCard.vue'
import SmartMeterMeasurementPointsCard from '../components/SmartMeterMeasurementPointsCard.vue'
import ImmichImageLinksCard from '../components/ImmichImageLinksCard.vue'
import { assetApi } from '../services/assetApi'
import { electricalApi } from '../services/electricalApi'
import type { Asset, AssetStatus, Product, Relationship } from '../types/assets'
import type { ElectricalConnection, ElectricalEndpoint, ElectricalTopology } from '../types/electrical'

const route = useRoute()
const router = useRouter()
const settings = useSettingsStore()
const activeModules = computed(() => new Set(settings.configuration?.enabled_modules ?? moduleKeys))
const selectedTab = ref('overview')
const returnTo = computed(() => inventoryReturnTo(route.query.return_to))
const supportingError = ref<string | null>(null)
let loadSequence = 0
const asset = ref<Asset | null>(null)
const product = ref<Product | null>(null)
const relationships = ref<Relationship[]>([])
const electricalTopology = ref<ElectricalTopology | null>(null)
const loading = ref(true)
const deleting = ref(false)
const confirmDelete = ref(false)
const duplicateOpen = ref(false)
const error = ref<string | null>(null)
const archivedView = computed(() => route.query.archived === '1')
const isSmartMeter = computed(() => {
  const name = asset.value?.asset_type.name.trim().toLocaleLowerCase('de') ?? ''
  return name.includes('smart meter') || name.includes('smartmeter')
})
const incomingConnections = computed(() => electricalTopology.value?.connections.filter(
  (connection) => connection.target.kind === 'asset' && connection.target.id === asset.value?.id
) ?? [])
const outgoingConnections = computed(() => electricalTopology.value?.connections.filter(
  (connection) => connection.source.kind === 'asset' && connection.source.id === asset.value?.id
) ?? [])

const statusText: Record<AssetStatus, string> = {
  active: 'Aktiv', inactive: 'Inaktiv', maintenance: 'Wartung', retired: 'Ausgemustert'
}
const contactTypeText: Record<string, string> = {
  normally_open: 'Schließer',
  normally_closed: 'Öffner',
  changeover: 'Wechsler'
}
const statusColor: Record<AssetStatus, string> = {
  active: 'success', inactive: 'secondary', maintenance: 'warning', retired: 'error'
}

watch([() => route.params.id, () => route.query.archived], async () => {
  const sequence = ++loadSequence
  const id = String(route.params.id)
  loading.value = true; error.value = null; supportingError.value = null
  asset.value = null; product.value = null; relationships.value = []; electricalTopology.value = null
  selectedTab.value = 'overview'
  try {
    const record = archivedView.value ? await assetApi.getArchived(id) : await assetApi.get(id)
    if (sequence !== loadSequence) return
    asset.value = record
    const [links, topology, model] = await Promise.all([
      assetApi.relationships(id).catch(() => { if (sequence === loadSequence) supportingError.value = 'Beziehungen konnten nicht geladen werden. Lade die Seite erneut, um sie zu prüfen.'; return [] }),
      activeModules.value.has('electrical') ? electricalApi.topology().catch(() => null) : Promise.resolve(null),
      record.product_id ? assetApi.getProduct(record.product_id).catch(() => null) : Promise.resolve(null)
    ])
    if (sequence !== loadSequence) return
    relationships.value = links; electricalTopology.value = topology; product.value = model
  } catch (reason) {
    if (sequence === loadSequence) error.value = reason instanceof Error ? reason.message : 'Gerät konnte nicht geladen werden.'
  } finally { if (sequence === loadSequence) loading.value = false }
}, { immediate: true })

async function removeAsset() {
  if (!asset.value || asset.value.deleted_at) return
  deleting.value = true
  error.value = null
  try {
    await assetApi.remove(asset.value.id)
    await router.push(returnTo.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Asset konnte nicht gelöscht werden.'
    confirmDelete.value = false
  } finally {
    deleting.value = false
  }
}

function endpointName(relationship: Relationship) {
  if (!asset.value) return ''
  return relationship.source_asset_id === asset.value.id
    ? `Ziel: ${relationship.target_asset_id}`
    : `Quelle: ${relationship.source_asset_id}`
}

function endpointRoute(endpoint: ElectricalEndpoint): string | null {
  if (endpoint.kind === 'asset') return `/assets/${endpoint.id}${endpoint.deleted_at ? '?archived=1' : ''}`
  if (endpoint.kind === 'distribution') return `/electrical/distributions/${endpoint.id}`
  if (endpoint.kind === 'protective_device') return `/electrical/protective-devices/${endpoint.id}/edit`
  if (endpoint.kind === 'circuit') return `/electrical/circuits/${endpoint.id}`
  return null
}

function connectionSubtitle(connection: ElectricalConnection): string {
  const phases = connection.effective_phases.length ? connection.effective_phases.join(', ') : 'Phase nicht zugeordnet'
  return [phases, connection.label, connection.cable_type].filter(Boolean).join(' · ')
}
</script>

<template>
 <v-container class="asset-detail" fluid>
  <v-btn variant="text" prepend-icon="mdi-arrow-left" :to="returnTo" class="mb-5 asset-back">Zurück zum Inventar</v-btn>
  <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />
  <v-alert v-else-if="error && !asset" type="error" variant="tonal">{{ error }}</v-alert>
  <template v-else-if="asset">
   <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
   <v-alert v-if="supportingError" type="warning" variant="tonal" class="mb-4">{{ supportingError }}</v-alert>
   <v-alert v-if="asset.deleted_at" type="warning" variant="tonal" class="mb-4">Archivierter Datensatz · {{ new Date(asset.deleted_at).toLocaleString('de-DE') }}. Dieses Gerät ist schreibgeschützt und bleibt als historischer Datensatz erhalten.</v-alert>
   <div class="asset-detail-header">
    <v-avatar rounded="lg" size="84" color="surface-variant" class="asset-detail-image"><v-img v-if="asset.effective_image_url || product?.image_url" :src="asset.effective_image_url || product?.image_url || undefined" :alt="`Bild von ${asset.name}`" contain/><v-icon v-else icon="mdi-package-variant" size="38"/></v-avatar>
    <div class="asset-detail-heading"><div class="home-eyebrow">{{ asset.jarvis_code }} · {{ asset.asset_type.name }}</div><h1>{{ asset.name }}</h1><p class="asset-detail-location"><v-icon icon="mdi-map-marker-outline" size="19"/>{{ asset.location?.name || 'Kein Ort zugeordnet' }}<v-chip :color="asset.deleted_at ? 'secondary' : statusColor[asset.status]" variant="tonal" size="small">{{ asset.deleted_at ? 'Archiviert' : statusText[asset.status] }}</v-chip></p></div>
    <div v-if="!asset.deleted_at" class="asset-detail-actions">
     <v-btn prepend-icon="mdi-pencil-outline" color="primary" :to="{ path: `/assets/${asset.id}/edit`, query: { return_to: route.fullPath } }">Bearbeiten</v-btn>
     <v-menu><template #activator="{ props }"><v-btn v-bind="props" icon="mdi-dots-horizontal" variant="outlined" aria-label="Weitere Aktionen" title="Weitere Aktionen"/></template><v-list><v-list-item title="Duplizieren" prepend-icon="mdi-content-copy" @click="duplicateOpen = true"/><v-list-item v-if="asset.status !== 'retired'" title="Ersetzen" prepend-icon="mdi-swap-horizontal" :to="`/assets/${asset.id}/replace`"/><v-list-item title="Archivieren" prepend-icon="mdi-archive-outline" @click="confirmDelete = true"/></v-list></v-menu>
    </div>
   </div>
   <v-tabs v-model="selectedTab" color="primary" class="asset-detail-tabs" show-arrows aria-label="Geräteakte"><v-tab value="overview">Übersicht</v-tab><v-tab value="media">Dokumente & Fotos</v-tab><v-tab value="activity">Wartung & Verlauf</v-tab><v-tab value="technology">Technik & Verknüpfungen</v-tab></v-tabs>
<v-row v-show="selectedTab === 'overview'" :key="`${asset.id}-overview`" class="mt-3"><v-col cols="12" lg="8"><v-card title="Das Wichtigste zum Gerät" prepend-icon="mdi-package-variant" class="mb-5">
            <v-card-text>
              <v-row>
                <v-col cols="12" sm="6"><div class="field-label">Produkt</div><div>{{ asset.product?.name || 'Nicht zugeordnet' }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">Ort</div><div>{{ asset.location?.name || 'Nicht zugeordnet' }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">DocOfHome-Code</div><div class="jarvis-code">{{ asset.jarvis_code }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">Inventarnummer</div><div>{{ asset.inventory_number || '–' }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">Seriennummer</div><div>{{ asset.serial_number || '–' }}</div></v-col>
                <v-col v-if="asset.effective_module_width" cols="12" sm="6"><div class="field-label">DIN-Breite</div><div>{{ asset.effective_module_width ? `${asset.effective_module_width} TE` : 'Nicht auf Hutschiene platzierbar' }}</div></v-col>
                <v-col v-if="asset.effective_breaker_characteristic" cols="12" sm="6"><div class="field-label">Auslösecharakteristik</div><div>{{ asset.effective_breaker_characteristic }}</div></v-col>
                <v-col v-if="asset.effective_rated_current_a" cols="12" sm="6"><div class="field-label">Nennstrom</div><div>{{ asset.effective_rated_current_a }} A<span v-if="asset.effective_breaker_characteristic"> · {{ asset.effective_breaker_characteristic }}{{ asset.effective_rated_current_a }}</span></div></v-col>
                <v-col v-if="asset.effective_coil_voltage_v" cols="12" sm="6"><div class="field-label">Spulenspannung</div><div>{{ asset.effective_coil_voltage_v }} V {{ asset.effective_coil_voltage_type || '' }}</div></v-col>
                <v-col v-if="asset.effective_contact_count" cols="12" sm="6"><div class="field-label">Schaltkontakte</div><div>{{ asset.effective_contact_count }} · {{ asset.effective_contact_type ? contactTypeText[asset.effective_contact_type] : 'Kontaktart nicht angegeben' }}</div></v-col>
                <v-col cols="12"><div class="field-label">Beschreibung</div><div class="description">{{ asset.description || 'Keine Beschreibung hinterlegt.' }}</div></v-col>
              </v-row>
            </v-card-text>
          </v-card>
<NotesCard target-type="asset" :target-id="asset.id" :read-only="Boolean(asset.deleted_at)" /></v-col><v-col cols="12" lg="4"><v-card v-if="product" title="Produktmodell" prepend-icon="mdi-package-variant-closed" class="mb-5">
            <v-img v-if="product.image_url" :src="product.image_url" :alt="`Produktbild ${product.name}`" height="230" contain class="product-image" />
            <v-card-text>
              <div class="text-h6">{{ product.name }}</div>
              <div class="text-medium-emphasis">{{ product.manufacturer || 'Hersteller unbekannt' }}<span v-if="product.model_number"> · {{ product.model_number }}</span></div>
              <p class="mt-3 mb-0">{{ product.description || 'Keine Produktbeschreibung hinterlegt.' }}</p>
            </v-card-text>
          </v-card>
          <v-card title="Labels" prepend-icon="mdi-label-multiple-outline" class="mb-5">
            <v-card-text>
              <div v-if="asset.labels.length" class="d-flex flex-wrap ga-2">
                <v-chip v-for="label in asset.labels" :key="label.id" :style="{ borderColor: label.color }" variant="outlined"><span class="label-dot mr-2" :style="{ backgroundColor: label.color }" />{{ label.name }}</v-chip>
              </div>
              <span v-else class="text-medium-emphasis">Keine Labels zugeordnet.</span>
            </v-card-text>
          </v-card><details class="asset-metadata"><summary>Metadaten</summary>
            <v-list density="compact">
              <v-list-item title="Erstellt" :subtitle="new Date(asset.created_at).toLocaleString()" />
              <v-list-item title="Zuletzt geändert" :subtitle="new Date(asset.updated_at).toLocaleString()" />
              <v-list-item v-if="asset.deleted_at" title="Archiviert" :subtitle="new Date(asset.deleted_at).toLocaleString()" />
              <v-list-item title="Asset-ID" :subtitle="asset.id" />
            </v-list>
          </details></v-col></v-row>
<section v-show="selectedTab === 'media'" :key="`${asset.id}-media`" class="asset-tab-content" aria-label="Dokumente und Fotos"><ImmichImageLinksCard v-if="activeModules.has('images')"
            :asset-id="asset.id"
            :read-only="Boolean(asset.deleted_at)"
            empty-text="Noch keine Immich-Fotos mit diesem Asset verknüpft."
          />
<DocumentLinksCard v-if="activeModules.has('documents')"
            target-type="asset"
            :target-id="asset.id"
            :read-only="Boolean(asset.deleted_at)"
          /><p v-if="!activeModules.has('images') && !activeModules.has('documents')" class="home-context-help">Bilder und Dokumente sind in den Moduleinstellungen deaktiviert.</p></section>
<section v-show="selectedTab === 'activity'" :key="`${asset.id}-activity`" class="asset-tab-content" aria-label="Wartung und Verlauf"><MaintenanceCard v-if="activeModules.has('maintenance')" target-type="asset" :target-id="asset.id" :read-only="Boolean(asset.deleted_at)" /><p v-if="!activeModules.has('maintenance')" class="home-context-help">Das Wartungsmodul ist in den Einstellungen deaktiviert.</p></section>
<section v-show="selectedTab === 'technology'" :key="`${asset.id}-technology`" class="asset-tab-content" aria-label="Technik und Verknüpfungen"><HomeAssistantAssetCard v-if="activeModules.has('smart_home')"
            :asset-id="asset.id"
            :read-only="Boolean(asset.deleted_at)"
          />
<SmartMeterMeasurementPointsCard
            v-if="isSmartMeter && activeModules.has('consumption')"
            :asset-id="asset.id"
            :read-only="Boolean(asset.deleted_at)"
          />
<ConsumptionMetersCard v-if="activeModules.has('consumption')" :asset-id="asset.id" />
<NetworkAssetCard v-if="activeModules.has('network')"
            :asset-id="asset.id"
            :asset-name="asset.name"
            :read-only="Boolean(asset.deleted_at)"
          />
<v-card title="Verbindungen" prepend-icon="mdi-source-branch" class="mb-5">
            <v-card-text v-if="!incomingConnections.length && !outgoingConnections.length" class="text-medium-emphasis">
              Keine direkten Versorgungsverbindungen dokumentiert.
            </v-card-text>
            <template v-else>
              <v-list v-if="incomingConnections.length" lines="two">
                <v-list-subheader>Einspeisung von</v-list-subheader>
                <v-list-item
                  v-for="connection in incomingConnections"
                  :key="connection.id"
                  :title="connection.source.name"
                  :subtitle="connectionSubtitle(connection)"
                  prepend-icon="mdi-arrow-right-bold-circle-outline"
                  :to="endpointRoute(connection.source) ?? undefined"
                />
              </v-list>
              <v-list v-if="outgoingConnections.length" lines="two">
                <v-list-subheader>Weiterführung zu</v-list-subheader>
                <v-list-item
                  v-for="connection in outgoingConnections"
                  :key="connection.id"
                  :title="connection.target.name"
                  :subtitle="connectionSubtitle(connection)"
                  prepend-icon="mdi-arrow-right-circle-outline"
                  :to="endpointRoute(connection.target) ?? undefined"
                />
              </v-list>
            </template>
          </v-card>
<v-card title="Beziehungen" prepend-icon="mdi-vector-link">
            <v-list v-if="relationships.length">
              <v-list-item v-for="relationship in relationships" :key="relationship.id" prepend-icon="mdi-link-variant">
                <v-list-item-title>{{ relationship.relationship_type }}</v-list-item-title>
                <v-list-item-subtitle>{{ relationship.description || endpointName(relationship) }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <v-card-text v-else class="text-medium-emphasis">Noch keine Beziehungen hinterlegt.</v-card-text>
          </v-card></section>
</template>
 <AssetDuplicateDialog v-model="duplicateOpen" :asset="asset" @saved="(items) => router.push(items.length === 1 ? { path: `/assets/${items[0].id}`, query: { return_to: returnTo } } : returnTo)"/>
 <v-dialog v-model="confirmDelete" max-width="480"><v-card title="Gerät archivieren?" prepend-icon="mdi-archive-outline"><v-card-text>„{{ asset?.name }}“ wird ausgeblendet, bleibt aber als historischer Datensatz erhalten.</v-card-text><v-card-actions><v-spacer/><v-btn @click="confirmDelete = false">Abbrechen</v-btn><v-btn color="warning" :loading="deleting" @click="removeAsset">Archivieren</v-btn></v-card-actions></v-card></v-dialog>
 </v-container>
</template>
<style scoped>
.asset-detail{max-width:1440px}.asset-back{padding-inline:0!important;color:var(--home-muted)}.asset-detail-header{display:flex;align-items:center;gap:23px;margin-bottom:28px}.asset-detail-heading{min-width:0;flex:1}.asset-detail-heading .home-eyebrow{letter-spacing:1px;font-size:11px}.asset-detail-heading h1{font-size:clamp(2rem,3vw,2.8rem)!important;overflow-wrap:anywhere}.asset-detail-location{display:flex;align-items:center;gap:10px;color:var(--home-muted);font-size:16px;margin-top:10px;flex-wrap:wrap}.asset-detail-location .v-chip{margin-left:10px}.asset-detail-actions{display:flex;gap:10px;align-items:center;flex-shrink:0}.asset-detail-tabs{max-width:100%;margin-bottom:20px}.asset-tab-content{padding-top:20px;max-width:1000px}.asset-tab-content>:deep(.v-card){margin-bottom:20px}.field-label{color:var(--home-muted);font-size:13px;margin-bottom:5px}.description{white-space:pre-wrap;overflow-wrap:anywhere}.jarvis-code{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-weight:600}.label-dot{display:inline-block;width:.65rem;height:.65rem;border-radius:50%}.product-image{background:var(--home-soft)}.asset-metadata{padding:20px 5px;color:var(--home-muted);font-size:14px}.asset-metadata summary{cursor:pointer;color:var(--home-ink);padding:8px}.asset-metadata :deep(.v-list){background:transparent}.asset-detail :deep(.v-list-item-subtitle){overflow-wrap:anywhere;white-space:normal}.asset-detail :deep(.v-list-item__append){max-width:100%}
@media(max-width:959px){.asset-detail-header{flex-wrap:wrap;gap:16px}.asset-detail-heading{flex-basis:calc(100% - 110px)}.asset-detail-actions{margin-left:auto}.asset-tab-content{max-width:100%}}
@media(max-width:599px){.asset-detail-image{width:66px!important;height:66px!important}.asset-detail-heading{flex-basis:calc(100% - 90px)}.asset-detail-heading .home-eyebrow{font-size:10px}.asset-detail-heading h1{font-size:2rem!important}.asset-detail-actions{width:100%;margin:0}.asset-detail-actions>.v-btn:first-child{flex:1}.asset-detail-location{font-size:14px;gap:5px}.asset-detail-location .v-chip{margin-left:6px}.asset-detail-tabs :deep(.v-tab){font-size:13px;min-width:0;padding-inline:13px}.asset-detail-tabs{margin-bottom:12px}.asset-tab-content :deep(.v-card-item){flex-wrap:wrap}.asset-tab-content :deep(.v-card-item__append){margin-left:0;max-width:100%}}
</style>
