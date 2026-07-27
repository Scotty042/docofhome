<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { homeAssistantApi } from '../services/homeAssistantApi'
import type {
  HomeAssistantAssetBindings,
  HomeAssistantDevice,
  HomeAssistantEntity,
  HomeAssistantEntityRole
} from '../types/homeAssistant'

const props = defineProps<{ modelValue: boolean; assetId: string }>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const deviceItems = ref<HomeAssistantDevice[]>([])
const entityItems = ref<HomeAssistantEntity[]>([])
const selectedDeviceIds = ref<Set<string>>(new Set())
const selectedEntities = ref<Map<string, HomeAssistantEntityRole>>(new Map())
const deviceSearch = ref('')
const entitySearch = ref('')
const entityDeviceId = ref<string | null>(null)
const devicePage = ref(1)
const entityPage = ref(1)
const deviceTotal = ref(0)
const entityTotal = ref(0)
const devicePageSize = 50
const entityPageSize = 100
let deviceTimer: ReturnType<typeof setTimeout> | undefined
let entityTimer: ReturnType<typeof setTimeout> | undefined

const devicePages = computed(() => Math.max(1, Math.ceil(deviceTotal.value / devicePageSize)))
const entityPages = computed(() => Math.max(1, Math.ceil(entityTotal.value / entityPageSize)))
const selectedDeviceOptions = computed(() => {
  const current = new Map(deviceItems.value.map((item) => [item.device_id, item.name]))
  return [...selectedDeviceIds.value].map((id) => ({ title: current.get(id) || id, value: id }))
})
const mayLoadEntities = computed(() => Boolean(
  entityDeviceId.value || entitySearch.value.trim().length >= 2
))

const roleOptions: Array<{ title: string; value: HomeAssistantEntityRole }> = [
  { title: 'Primäre Live-Anzeige', value: 'primary_live' },
  { title: 'Gesamtleistung', value: 'total_power' },
  { title: 'Spannung', value: 'voltage' },
  { title: 'Stromstärke', value: 'current' },
  { title: 'Energiezähler', value: 'energy' },
  { title: 'Leistung L1', value: 'power_l1' },
  { title: 'Leistung L2', value: 'power_l2' },
  { title: 'Leistung L3', value: 'power_l3' },
  { title: 'Spannung L1', value: 'voltage_l1' },
  { title: 'Spannung L2', value: 'voltage_l2' },
  { title: 'Spannung L3', value: 'voltage_l3' },
  { title: 'Schaltausgang', value: 'switch_output' },
  { title: 'Eingang', value: 'input' },
  { title: 'Verfügbarkeit', value: 'availability' },
  { title: 'Diagnose', value: 'diagnostic' },
  { title: 'Weitere Information', value: 'additional' }
]

watch(() => props.modelValue, (open) => {
  if (open) void initialize()
})
watch(deviceSearch, () => {
  devicePage.value = 1
  clearTimeout(deviceTimer)
  deviceTimer = setTimeout(() => void loadDevices(), 300)
})
watch(entitySearch, () => {
  entityPage.value = 1
  clearTimeout(entityTimer)
  entityTimer = setTimeout(() => void loadEntities(), 300)
})
watch(devicePage, () => void loadDevices())
watch(entityPage, () => void loadEntities())
watch(entityDeviceId, () => {
  entityPage.value = 1
  void loadEntities()
})

async function initialize() {
  loading.value = true
  error.value = null
  deviceSearch.value = ''
  entitySearch.value = ''
  devicePage.value = 1
  entityPage.value = 1
  entityItems.value = []
  try {
    const [bindings] = await Promise.all([
      homeAssistantApi.assetBindings(props.assetId),
      loadDevices()
    ])
    applyBindings(bindings)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Zuordnungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function applyBindings(bindings: HomeAssistantAssetBindings) {
  selectedDeviceIds.value = new Set(bindings.device_links.map((link) => link.external_id))
  selectedEntities.value = new Map(bindings.entity_links.map((link) => [link.external_id, link.role]))
  if (!entityDeviceId.value && selectedDeviceIds.value.size) {
    entityDeviceId.value = [...selectedDeviceIds.value][0]
  }
}

async function loadDevices() {
  const result = await homeAssistantApi.devices({
    search: deviceSearch.value.trim() || undefined,
    offset: (devicePage.value - 1) * devicePageSize,
    limit: devicePageSize,
    selection_scope: 'all'
  })
  deviceItems.value = result.items
  deviceTotal.value = result.total
}

async function loadEntities() {
  if (!mayLoadEntities.value) {
    entityItems.value = []
    entityTotal.value = 0
    return
  }
  try {
    const result = await homeAssistantApi.entities({
      search: entitySearch.value.trim() || undefined,
      device_id: entityDeviceId.value || undefined,
      offset: (entityPage.value - 1) * entityPageSize,
      limit: entityPageSize,
      selection_scope: 'all'
    })
    entityItems.value = result.items
    entityTotal.value = result.total
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Entitäten konnten nicht geladen werden.'
  }
}

function toggleDevice(id: string) {
  const next = new Set(selectedDeviceIds.value)
  if (next.has(id)) {
    next.delete(id)
    if (entityDeviceId.value === id) entityDeviceId.value = [...next][0] || null
  } else {
    next.add(id)
    entityDeviceId.value ||= id
  }
  selectedDeviceIds.value = next
}

function toggleEntity(id: string) {
  const next = new Map(selectedEntities.value)
  if (next.has(id)) next.delete(id)
  else next.set(id, 'additional')
  selectedEntities.value = next
}

function setRole(id: string, role: HomeAssistantEntityRole) {
  const next = new Map(selectedEntities.value)
  if (role === 'primary_live') {
    for (const [entityId, existingRole] of next) {
      if (existingRole === 'primary_live' && entityId !== id) next.set(entityId, 'additional')
    }
  }
  next.set(id, role)
  selectedEntities.value = next
}

async function save() {
  saving.value = true
  error.value = null
  try {
    await homeAssistantApi.replaceAssetBindings(props.assetId, {
      device_ids: [...selectedDeviceIds.value],
      entities: [...selectedEntities.value].map(([external_id, role]) => ({ external_id, role }))
    })
    emit('saved')
    emit('update:modelValue', false)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Zuordnungen konnten nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-dialog
    :model-value="modelValue"
    max-width="1100"
    scrollable
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card title="Home Assistant zuordnen" prepend-icon="mdi-home-assistant">
      <v-progress-linear v-if="loading" indeterminate />
      <v-card-text>
        <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
        <v-alert type="info" variant="tonal" density="compact" class="mb-4">
          Geräte und Entitäten werden serverseitig seitenweise geladen. Bereits markierte Einträge bleiben beim Suchen und Blättern erhalten.
        </v-alert>
        <v-row>
          <v-col cols="12" md="5">
            <div class="text-subtitle-1 font-weight-bold mb-2">Geräte</div>
            <v-text-field
              v-model="deviceSearch"
              label="Geräte suchen"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              class="mb-3"
            />
            <v-list border rounded density="compact" lines="two">
              <v-list-item
                v-for="device in deviceItems"
                :key="device.device_id"
                :title="device.name"
                :subtitle="[device.manufacturer, device.model, device.area_name].filter(Boolean).join(' · ') || device.device_id"
                @click="toggleDevice(device.device_id)"
              >
                <template #prepend>
                  <v-checkbox-btn
                    :model-value="selectedDeviceIds.has(device.device_id)"
                    @click.stop="toggleDevice(device.device_id)"
                  />
                </template>
              </v-list-item>
            </v-list>
            <v-pagination
              v-if="devicePages > 1"
              v-model="devicePage"
              :length="devicePages"
              :total-visible="5"
              density="compact"
              class="mt-3"
            />
          </v-col>

          <v-col cols="12" md="7">
            <div class="text-subtitle-1 font-weight-bold mb-2">Entitäten mit Funktion</div>
            <v-row dense class="mb-2">
              <v-col cols="12" sm="6">
                <v-select
                  v-model="entityDeviceId"
                  :items="selectedDeviceOptions"
                  label="Entitäten eines gewählten Geräts"
                  clearable
                  hide-details
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="entitySearch"
                  label="Oder mindestens 2 Zeichen suchen"
                  prepend-inner-icon="mdi-magnify"
                  clearable
                  hide-details
                />
              </v-col>
            </v-row>
            <v-alert v-if="!mayLoadEntities" type="info" variant="tonal" density="compact">
              Wähle zuerst ein Gerät oder gib mindestens zwei Suchzeichen ein. Dadurch werden nicht alle Entitäten auf einmal geladen.
            </v-alert>
            <v-list v-else border rounded density="compact" lines="two">
              <v-list-item
                v-for="entity in entityItems"
                :key="entity.entity_id"
                :title="entity.name"
                :subtitle="`${entity.entity_id}${entity.device_name ? ` · ${entity.device_name}` : ''}`"
              >
                <template #prepend>
                  <v-checkbox-btn
                    :model-value="selectedEntities.has(entity.entity_id)"
                    @click="toggleEntity(entity.entity_id)"
                  />
                </template>
                <template #append>
                  <v-select
                    v-if="selectedEntities.has(entity.entity_id)"
                    :model-value="selectedEntities.get(entity.entity_id)"
                    :items="roleOptions"
                    density="compact"
                    hide-details
                    style="min-width: 190px"
                    @update:model-value="setRole(entity.entity_id, $event)"
                  />
                </template>
              </v-list-item>
            </v-list>
            <v-pagination
              v-if="entityPages > 1"
              v-model="entityPage"
              :length="entityPages"
              :total-visible="5"
              density="compact"
              class="mt-3"
            />
            <div class="d-flex flex-wrap ga-2 mt-4">
              <v-chip color="primary" variant="tonal">{{ selectedDeviceIds.size }} Geräte</v-chip>
              <v-chip color="primary" variant="tonal">{{ selectedEntities.size }} Entitäten</v-chip>
            </div>
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" :disabled="saving" @click="emit('update:modelValue', false)">Abbrechen</v-btn>
        <v-btn color="primary" prepend-icon="mdi-content-save" :loading="saving" @click="save">
          Zuordnungen speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
