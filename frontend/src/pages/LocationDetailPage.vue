<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import DocumentLinksCard from '../components/DocumentLinksCard.vue'
import ConsumptionMetersCard from '../components/ConsumptionMetersCard.vue'
import MaintenanceCard from '../components/MaintenanceCard.vue'
import NotesCard from '../components/NotesCard.vue'
import { useLocationDetailData } from '../composables/useLocationDetailData'
import { LocationApiError, locationApi } from '../services/locationApi'
import { LOCATION_ASSET_PAGE_SIZES } from '../services/locationAssets'
import { locationTypeIcon, locationTypeLabel } from '../services/locationPresentation'

const route = useRoute()
const router = useRouter()
const deleting = ref(false)
const {
  location,
  assets,
  loading,
  assetsLoading,
  confirmArchive,
  error,
  errorStatus,
  assetError,
  assetTotal,
  assetPages,
  assetPage,
  assetPageSize,
  loadAssets,
  reloadAssetsFromFirstPage,
  loadLocation
} = useLocationDetailData()
const locationId = computed(() => String(route.params.id ?? ''))

const totalAssets = computed(() => (
  (location.value?.direct_asset_count ?? 0) + (location.value?.descendant_asset_count ?? 0)
))
const unavailable = computed(() => errorStatus.value === 0 || (errorStatus.value ?? 0) >= 500)
const breadcrumbItems = computed(() => location.value?.breadcrumbs.map((item, index, values) => ({
  title: item.name,
  to: index < values.length - 1 ? `/locations/${item.id}` : undefined,
  disabled: index === values.length - 1
})) ?? [])

async function archiveLocation() {
  if (!location.value) return
  deleting.value = true
  error.value = null
  try {
    await locationApi.remove(location.value.id)
    await router.push('/locations')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Bereich konnte nicht archiviert werden.'
    errorStatus.value = reason instanceof LocationApiError ? reason.status : 0
    confirmArchive.value = false
  } finally {
    deleting.value = false
  }
}

watch(locationId, (id) => void loadLocation(id), { immediate: true })
</script>

<template>
  <v-container class="location-detail pa-4 pa-sm-6" fluid>
    <v-btn variant="text" prepend-icon="mdi-arrow-left" to="/locations" class="mb-2">
      Zur Standortübersicht
    </v-btn>
    <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />
    <v-alert v-else-if="error && !location" :type="unavailable ? 'warning' : 'error'" variant="tonal">
      {{ unavailable ? 'Backend nicht erreichbar: ' : '' }}{{ error }}
    </v-alert>

    <template v-else-if="location">
      <v-breadcrumbs :items="breadcrumbItems" class="px-0 mb-2" />
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-alert v-if="location.deleted_at" type="warning" variant="tonal" class="mb-4">
        Dieser Standort ist archiviert und bleibt nur für historische Zuordnungen lesbar.
      </v-alert>

      <div class="d-flex flex-wrap align-start justify-space-between ga-3 mb-5">
        <div>
          <div class="d-flex align-center ga-3">
            <v-icon :icon="locationTypeIcon(location.location_type)" size="36" color="secondary" />
            <h1>{{ location.name }}</h1>
          </div>
          <p class="text-medium-emphasis mb-0">
            {{ locationTypeLabel(location.location_type) }} · {{ location.path }}
          </p>
        </div>
        <div v-if="!location.deleted_at" class="d-flex ga-2">
          <v-btn prepend-icon="mdi-plus" variant="tonal" :to="`/locations/new?parent=${location.id}`">
            Unterbereich
          </v-btn>
          <v-btn prepend-icon="mdi-pencil" color="primary" :to="`/locations/${location.id}/edit`">
            Bearbeiten
          </v-btn>
          <v-btn
            v-if="location.parent_id"
            icon="mdi-archive-arrow-down-outline"
            color="warning"
            variant="tonal"
            aria-label="Standort archivieren"
            title="Standort archivieren"
            @click="confirmArchive = true"
          />
        </div>
      </div>

      <v-row>
        <v-col cols="12" lg="8">
          <v-card title="Standortdaten" prepend-icon="mdi-map-marker-outline" class="mb-5">
            <v-card-text>
              <v-row>
                <v-col cols="12" sm="6"><div class="field-label">Kurzname</div><div>{{ location.short_name || '–' }}</div></v-col>
                <v-col cols="12" sm="6"><div class="field-label">Sortierreihenfolge</div><div>{{ location.sort_order ?? '–' }}</div></v-col>
                <v-col cols="12"><div class="field-label">Beschreibung</div><div class="pre-wrap">{{ location.description || 'Keine Beschreibung hinterlegt.' }}</div></v-col>
                <v-col cols="12"><div class="field-label">Notizen</div><div class="pre-wrap">{{ location.notes || 'Keine Notizen hinterlegt.' }}</div></v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <v-card title="Direkt zugeordnete Assets" prepend-icon="mdi-package-variant">
            <v-progress-linear v-if="assetsLoading" indeterminate color="primary" />
            <v-alert v-if="assetError" type="error" variant="tonal" class="ma-4">
              {{ assetError }}
            </v-alert>
            <v-list v-else-if="assets.length" lines="two">
              <v-list-item
                v-for="asset in assets"
                :key="asset.id"
                :title="asset.name"
                :subtitle="`${asset.jarvis_code} · ${asset.asset_type.name}`"
                :to="`/assets/${asset.id}`"
                prepend-icon="mdi-package-variant-closed"
              />
            </v-list>
            <v-card-text v-else-if="!assetsLoading" class="text-medium-emphasis">
              Noch keine Assets direkt an diesem Standort.
            </v-card-text>
            <v-divider v-if="assetTotal && !assetError" />
            <v-card-actions
              v-if="assetTotal && !assetError"
              class="flex-wrap justify-space-between px-4 py-3"
            >
              <span class="text-body-2 text-medium-emphasis">
                {{ assetTotal }} Asset{{ assetTotal === 1 ? '' : 's' }} direkt zugeordnet
              </span>
              <div class="d-flex align-center ga-3">
                <v-select
                  v-model="assetPageSize"
                  :items="LOCATION_ASSET_PAGE_SIZES"
                  density="compact"
                  hide-details
                  style="width: 90px"
                  aria-label="Direkte Assets pro Seite"
                  @update:model-value="reloadAssetsFromFirstPage"
                />
                <v-pagination
                  v-model="assetPage"
                  :length="assetPages"
                  :total-visible="5"
                  density="comfortable"
                  aria-label="Seiten der direkt zugeordneten Assets"
                  @update:model-value="loadAssets()"
                />
              </div>
            </v-card-actions>
          </v-card>
        </v-col>
        <v-col cols="12" lg="4">
          <v-card title="Asset-Übersicht" prepend-icon="mdi-counter" class="mb-5">
            <v-list>
              <v-list-item title="Direkt" :subtitle="String(location.direct_asset_count)" />
              <v-list-item title="In Unterbereichen" :subtitle="String(location.descendant_asset_count)" />
              <v-list-item title="Gesamt" :subtitle="String(totalAssets)" />
            </v-list>
          </v-card>
          <v-card title="Metadaten" prepend-icon="mdi-clock-outline">
            <v-list density="compact">
              <v-list-item title="Erstellt" :subtitle="new Date(location.created_at).toLocaleString()" />
              <v-list-item title="Zuletzt geändert" :subtitle="new Date(location.updated_at).toLocaleString()" />
              <v-list-item title="Location-ID" :subtitle="location.id" />
            </v-list>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <ConsumptionMetersCard
      v-if="location"
      :location-id="location.id"
      title="Verbrauchszähler an diesem Standort"
      class="mt-5"
    />

    <DocumentLinksCard
      v-if="location"
      target-type="location"
      :target-id="location.id"
      :read-only="Boolean(location.deleted_at)"
      class="mt-5"
    />

    <NotesCard
      v-if="location"
      target-type="location"
      :target-id="location.id"
      :read-only="Boolean(location.deleted_at)"
      class="mt-5"
    />
    <MaintenanceCard
      v-if="location"
      target-type="location"
      :target-id="location.id"
      :read-only="Boolean(location.deleted_at)"
      class="mt-5"
    />

    <v-dialog v-model="confirmArchive" max-width="520">
      <v-card title="Standort archivieren?" prepend-icon="mdi-alert-outline">
        <v-card-text>
          „{{ location?.name }}“ wird aus aktiven Ansichten ausgeblendet. Aktive Kinder oder Assets
          müssen vorher verschoben werden; historische Daten bleiben erhalten.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="confirmArchive = false">Abbrechen</v-btn>
          <v-btn color="warning" :loading="deleting" @click="archiveLocation">Archivieren</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.location-detail { max-width: 1280px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.4rem); }
.field-label { color: rgb(var(--v-theme-secondary)); font-size: .8rem; margin-bottom: .2rem; }
.pre-wrap { white-space: pre-wrap; }
</style>
