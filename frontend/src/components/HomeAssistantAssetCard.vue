<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import HomeAssistantAssetBindingsDialog from './HomeAssistantAssetBindingsDialog.vue'

import { homeAssistantApi } from '../services/homeAssistantApi'
import type {
  HomeAssistantAssetBindings,
  HomeAssistantAssetLink,
  HomeAssistantDevice,
  HomeAssistantEntity
} from '../types/homeAssistant'

const props = defineProps<{ assetId: string; readOnly?: boolean }>()
const bindings = ref<HomeAssistantAssetBindings | null>(null)
const loading = ref(false)
const removingId = ref<string | null>(null)
const error = ref<string | null>(null)
const editDialog = ref(false)

const deviceById = computed(() => new Map(
  (bindings.value?.devices ?? []).map((device) => [device.device_id, device])
))
const entityById = computed(() => new Map(
  (bindings.value?.entities ?? []).map((entity) => [entity.entity_id, entity])
))
const hasLinks = computed(() => Boolean(
  bindings.value?.device_links.length || bindings.value?.entity_links.length
))

async function load(refresh = false) {
  loading.value = true
  error.value = null
  try {
    bindings.value = await homeAssistantApi.assetBindings(props.assetId, refresh)
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Home-Assistant-Zuordnungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function removeLink(link: HomeAssistantAssetLink) {
  removingId.value = link.id
  error.value = null
  try {
    await homeAssistantApi.removeLink(link.object_type, link.external_id)
    await load()
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Home-Assistant-Zuordnung konnte nicht entfernt werden.'
  } finally {
    removingId.value = null
  }
}

function deviceTitle(link: HomeAssistantAssetLink): string {
  return deviceById.value.get(link.external_id)?.name ?? link.external_id
}

function deviceSubtitle(device: HomeAssistantDevice | undefined): string {
  if (!device) return 'Das Gerät ist aktuell nicht über Home Assistant erreichbar.'
  return [device.manufacturer, device.model, device.area_name].filter(Boolean).join(' · ')
    || device.device_id
}

function entityIcon(entity: HomeAssistantEntity | undefined): string {
  const icon = entity?.icon?.trim()
  if (!icon) return 'mdi-access-point'
  return icon.startsWith('mdi:') ? icon.replace('mdi:', 'mdi-') : icon
}

function formatState(entity: HomeAssistantEntity | undefined): string {
  if (!entity) return 'Nicht verfügbar'
  return entity.unit ? `${entity.state} ${entity.unit}` : entity.state
}

function formatTimestamp(value: string | null): string {
  return value ? new Date(value).toLocaleString() : 'Unbekannt'
}

onMounted(() => void load())
watch(() => props.assetId, () => void load())
</script>

<template>
  <v-card title="Home Assistant" prepend-icon="mdi-home-assistant" class="mb-5">
    <template #append>
      <div class="d-flex ga-2">
        <v-btn
          size="small"
          variant="text"
          icon="mdi-refresh"
          aria-label="Home-Assistant-Daten aktualisieren"
          title="Home-Assistant-Daten aktualisieren"
          :loading="loading"
          @click="load(true)"
        />
        <v-btn
          v-if="!readOnly"
          size="small"
          variant="tonal"
          prepend-icon="mdi-link-variant-plus"
          @click="editDialog = true"
        >Bearbeiten</v-btn>
        <v-btn
          size="small"
          variant="text"
          prepend-icon="mdi-open-in-new"
          to="/smart-home"
        >Übersicht</v-btn>
      </div>
    </template>

    <v-progress-linear v-if="loading" indeterminate />
    <v-alert v-if="error" type="error" variant="tonal" class="ma-4 mb-0">
      {{ error }}
    </v-alert>
    <v-alert v-if="bindings?.warning" type="warning" variant="tonal" class="ma-4 mb-0">
      {{ bindings.warning }} Die gespeicherten Zuordnungen bleiben trotzdem sichtbar.
    </v-alert>

    <template v-if="hasLinks">
      <v-card-text v-if="bindings?.device_links.length" class="pb-2">
        <div class="text-subtitle-1 font-weight-bold mb-2">Verknüpfte Geräte</div>
        <v-list density="compact" lines="two" border rounded>
          <v-list-item
            v-for="link in (bindings?.device_links ?? [])"
            :key="link.id"
            prepend-icon="mdi-devices"
            :title="deviceTitle(link)"
            :subtitle="deviceSubtitle(deviceById.get(link.external_id))"
          >
            <template #append>
              <v-btn
                v-if="!readOnly"
                icon="mdi-link-variant-off"
                size="small"
                variant="text"
                color="error"
                aria-label="Gerätezuordnung entfernen"
                title="Gerätezuordnung entfernen"
                :loading="removingId === link.id"
                @click="removeLink(link)"
              />
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>

      <v-card-text v-if="bindings?.entity_links.length" class="pt-3">
        <div class="d-flex flex-wrap align-center justify-space-between ga-2 mb-2">
          <div>
            <div class="text-subtitle-1 font-weight-bold">Home-Assistant-Eigenschaften</div>
            <div class="text-caption text-medium-emphasis">
              Entitäten bleiben Home-Assistant-Zustände und werden nicht als zusätzliche Assets angelegt.
            </div>
          </div>
          <v-chip size="small" variant="tonal" prepend-icon="mdi-access-point">
            {{ bindings?.entity_links.length ?? 0 }} Entitäten
          </v-chip>
        </div>
        <v-list density="compact" lines="three" border rounded>
          <v-list-item
            v-for="link in (bindings?.entity_links ?? [])"
            :key="link.id"
            :prepend-icon="entityIcon(entityById.get(link.external_id))"
          >
            <v-list-item-title>
              {{ entityById.get(link.external_id)?.name || link.external_id }}
            </v-list-item-title>
            <v-list-item-subtitle>
              {{ link.external_id }}
              <template v-if="entityById.get(link.external_id)?.device_name">
                · {{ entityById.get(link.external_id)?.device_name }}
              </template>
            </v-list-item-subtitle>
            <v-list-item-subtitle class="d-flex flex-wrap ga-2 align-center">
              <v-chip size="x-small" color="primary" variant="tonal">{{ link.role }}</v-chip>
              <span>Aktualisiert: {{ formatTimestamp(entityById.get(link.external_id)?.last_updated ?? null) }}</span>
            </v-list-item-subtitle>
            <template #append>
              <div class="d-flex align-center ga-2 property-actions">
                <v-chip
                  :color="entityById.get(link.external_id)?.available ? 'success' : 'warning'"
                  variant="tonal"
                  class="state-chip"
                >
                  {{ formatState(entityById.get(link.external_id)) }}
                </v-chip>
                <v-btn
                  v-if="!readOnly"
                  icon="mdi-link-variant-off"
                  size="small"
                  variant="text"
                  color="error"
                  aria-label="Entitätszuordnung entfernen"
                  title="Entitätszuordnung entfernen"
                  :loading="removingId === link.id"
                  @click="removeLink(link)"
                />
              </div>
            </template>
          </v-list-item>
        </v-list>
      </v-card-text>
    </template>

    <v-card-text v-else-if="!loading" class="text-medium-emphasis">
      Noch kein Home-Assistant-Gerät und keine Entität sind diesem Asset zugeordnet.
      Ein physisches Home-Assistant-Gerät entspricht normalerweise einem Asset; seine Sensoren,
      Messwerte und Schalter werden anschließend als Eigenschaften desselben Assets verknüpft.
    </v-card-text>
    <HomeAssistantAssetBindingsDialog
      v-model="editDialog"
      :asset-id="assetId"
      @saved="load()"
    />
  </v-card>
</template>

<style scoped>
.property-actions {
  max-width: min(420px, 48vw);
}

.state-chip {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
}

@media (max-width: 700px) {
  .property-actions {
    align-items: flex-end;
    flex-direction: column;
    max-width: 42vw;
  }
}
</style>
