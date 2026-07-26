<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AssetDuplicateDialog from '../components/AssetDuplicateDialog.vue'
import DocumentLinksCard from '../components/DocumentLinksCard.vue'
import ConsumptionMetersCard from '../components/ConsumptionMetersCard.vue'
import HomeAssistantAssetCard from '../components/HomeAssistantAssetCard.vue'
import MaintenanceCard from '../components/MaintenanceCard.vue'
import NetworkAssetCard from '../components/NetworkAssetCard.vue'
import NotesCard from '../components/NotesCard.vue'
import ImmichImageLinksCard from '../components/ImmichImageLinksCard.vue'
import { assetApi } from '../services/assetApi'
import type { Asset, AssetStatus, Product, Relationship } from '../types/assets'

const route = useRoute()
const router = useRouter()
const asset = ref<Asset | null>(null)
const product = ref<Product | null>(null)
const relationships = ref<Relationship[]>([])
const loading = ref(true)
const deleting = ref(false)
const confirmDelete = ref(false)
const duplicateOpen = ref(false)
const error = ref<string | null>(null)
const archivedView = computed(() => route.query.archived === '1')

const statusText: Record<AssetStatus, string> = {
  active: 'Aktiv', inactive: 'Inaktiv', maintenance: 'Wartung', retired: 'Ausgemustert'
}
const statusColor: Record<AssetStatus, string> = {
  active: 'success', inactive: 'secondary', maintenance: 'warning', retired: 'error'
}

onMounted(async () => {
  try {
    const id = String(route.params.id)
    const record = archivedView.value ? await assetApi.getArchived(id) : await assetApi.get(id)
    asset.value = record
    relationships.value = await assetApi.relationships(id)
    if (record.product_id) {
      try {
        product.value = await assetApi.getProduct(record.product_id)
      } catch {
        product.value = null
      }
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Asset konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
})

async function removeAsset() {
  if (!asset.value || asset.value.deleted_at) return
  deleting.value = true
  error.value = null
  try {
    await assetApi.remove(asset.value.id)
    await router.push('/assets')
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
</script>

<template>
  <v-container class="asset-detail pa-4 pa-sm-6" fluid>
    <v-btn variant="text" prepend-icon="mdi-arrow-left" to="/assets" class="mb-3">Zur Assetliste</v-btn>
    <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />
    <v-alert v-else-if="error && !asset" type="error" variant="tonal">{{ error }}</v-alert>

    <template v-else-if="asset">
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert v-if="asset.deleted_at" type="warning" variant="tonal" class="mb-4">
        <strong>Archivierter Datensatz:</strong> Dieses Asset wurde am
        {{ new Date(asset.deleted_at).toLocaleString() }} archiviert und ist nur noch lesbar.
        Wiederherstellen wird erst mit einem gesicherten Konflikt- und Prüfworkflow ergänzt.
      </v-alert>

      <div class="d-flex flex-wrap align-start justify-space-between ga-3 mb-5">
        <div class="d-flex align-center ga-4">
          <v-avatar rounded="lg" size="92" color="surface-variant">
            <v-img v-if="product?.image_url" :src="product.image_url" :alt="`Produktbild ${asset.name}`" contain />
            <v-icon v-else icon="mdi-package-variant" size="42" />
          </v-avatar>
          <div>
            <div class="d-flex flex-wrap align-center ga-3">
              <h1>{{ asset.name }}</h1>
              <v-chip v-if="asset.deleted_at" color="secondary" variant="tonal" prepend-icon="mdi-archive-outline">
                Archiviert
              </v-chip>
              <v-chip v-else :color="statusColor[asset.status]" variant="tonal">{{ statusText[asset.status] }}</v-chip>
            </div>
            <p class="text-medium-emphasis mb-0">
              <span class="jarvis-code">{{ asset.jarvis_code }}</span> · {{ asset.asset_type.name }}
            </p>
          </div>
        </div>
        <div v-if="!asset.deleted_at" class="d-flex ga-2">
          <v-btn prepend-icon="mdi-content-copy" variant="tonal" @click="duplicateOpen = true">Duplizieren</v-btn>
          <v-btn v-if="asset.status !== 'retired'" prepend-icon="mdi-swap-horizontal" variant="tonal" :to="`/assets/${asset.id}/replace`">Ersetzen</v-btn>
          <v-btn prepend-icon="mdi-pencil" color="primary" :to="`/assets/${asset.id}/edit`">Bearbeiten</v-btn>
          <v-btn icon="mdi-delete-outline" color="error" variant="tonal" aria-label="Asset löschen" title="Asset archivieren" @click="confirmDelete = true" />
        </div>
      </div>

      <v-row>
        <v-col cols="12" lg="8">
          <v-card title="Assetdaten" prepend-icon="mdi-package-variant" class="mb-5">
            <v-card-text>
              <v-alert type="info" variant="tonal" density="compact" class="mb-4">
                Der DocOfHome-Code identifiziert den Datensatz automatisch. Inventarnummer und Seriennummer sind optionale reale Kennungen.
              </v-alert>
              <v-row>
                <v-col cols="12" sm="6"><div class="field-label">Produkt</div><div>{{ asset.product?.name || 'Nicht zugeordnet' }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">Ort</div><div>{{ asset.location?.name || 'Nicht zugeordnet' }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">DocOfHome-Code</div><div class="jarvis-code">{{ asset.jarvis_code }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">Inventarnummer</div><div>{{ asset.inventory_number || '–' }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">Seriennummer</div><div>{{ asset.serial_number || '–' }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">DIN-Breite</div><div>{{ asset.effective_module_width ? `${asset.effective_module_width} TE` : 'Nicht auf Hutschiene platzierbar' }}</div></v-col>
                <v-col cols="12"><div class="field-label">Beschreibung</div><div class="description">{{ asset.description || 'Keine Beschreibung hinterlegt.' }}</div></v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <HomeAssistantAssetCard
            :asset-id="asset.id"
            :read-only="Boolean(asset.deleted_at)"
          />

          <ConsumptionMetersCard :asset-id="asset.id" />

          <NetworkAssetCard
            :asset-id="asset.id"
            :asset-name="asset.name"
            :read-only="Boolean(asset.deleted_at)"
          />

          <ImmichImageLinksCard
            :asset-id="asset.id"
            :read-only="Boolean(asset.deleted_at)"
            empty-text="Noch keine Immich-Fotos mit diesem Asset verknüpft."
          />

          <DocumentLinksCard
            target-type="asset"
            :target-id="asset.id"
            :read-only="Boolean(asset.deleted_at)"
          />

          <NotesCard target-type="asset" :target-id="asset.id" :read-only="Boolean(asset.deleted_at)" />
          <MaintenanceCard target-type="asset" :target-id="asset.id" :read-only="Boolean(asset.deleted_at)" />

          <v-card title="Beziehungen" prepend-icon="mdi-vector-link">
            <v-list v-if="relationships.length">
              <v-list-item v-for="relationship in relationships" :key="relationship.id" prepend-icon="mdi-link-variant">
                <v-list-item-title>{{ relationship.relationship_type }}</v-list-item-title>
                <v-list-item-subtitle>{{ relationship.description || endpointName(relationship) }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
            <v-card-text v-else class="text-medium-emphasis">Noch keine Beziehungen hinterlegt.</v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" lg="4">
          <v-card v-if="product" title="Produktmodell" prepend-icon="mdi-package-variant-closed" class="mb-5">
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
          </v-card>
          <v-card title="Metadaten" prepend-icon="mdi-clock-outline">
            <v-list density="compact">
              <v-list-item title="Erstellt" :subtitle="new Date(asset.created_at).toLocaleString()" />
              <v-list-item title="Zuletzt geändert" :subtitle="new Date(asset.updated_at).toLocaleString()" />
              <v-list-item v-if="asset.deleted_at" title="Archiviert" :subtitle="new Date(asset.deleted_at).toLocaleString()" />
              <v-list-item title="Asset-ID" :subtitle="asset.id" />
            </v-list>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <AssetDuplicateDialog
      v-model="duplicateOpen"
      :asset="asset"
      @saved="(items) => router.push(items.length === 1 ? `/assets/${items[0].id}` : '/assets')"
    />

    <v-dialog v-model="confirmDelete" max-width="480">
      <v-card title="Asset archivieren?" prepend-icon="mdi-archive-outline">
        <v-card-text>„{{ asset?.name }}“ wird ausgeblendet, bleibt aber als historischer Datensatz erhalten.</v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="confirmDelete = false">Abbrechen</v-btn><v-btn color="warning" :loading="deleting" @click="removeAsset">Archivieren</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.asset-detail { max-width: 1280px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.4rem); }
.field-label { color: rgb(var(--v-theme-secondary)); font-size: .8rem; margin-bottom: .2rem; }
.description { white-space: pre-wrap; }
.label-dot { display: inline-block; width: .65rem; height: .65rem; border-radius: 50%; }
.jarvis-code { font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-weight: 700; }
.product-image { background: rgba(var(--v-theme-on-surface), .04); }
</style>
