<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { electricalApi } from '../services/electricalApi'
import { homeAssistantApi } from '../services/homeAssistantApi'
import { smartMeterApi } from '../services/smartMeterApi'
import type {
  ElectricalConnection,
  SmartMeterMeasurementEntityRole,
  SmartMeterMeasurementPoint,
  SmartMeterMeasurementPointWrite
} from '../types/electrical'
import type { HomeAssistantEntity } from '../types/homeAssistant'

const props = defineProps<{ assetId: string; readOnly?: boolean }>()

const points = ref<SmartMeterMeasurementPoint[]>([])
const connections = ref<ElectricalConnection[]>([])
const entities = ref<HomeAssistantEntity[]>([])
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const editorOpen = ref(false)
const editingId = ref<string | null>(null)
const confirmDelete = ref<SmartMeterMeasurementPoint | null>(null)

const emptyForm = (): SmartMeterMeasurementPointWrite => ({
  connection_id: '',
  channel_name: '',
  name: '',
  phase: null,
  direction: 'unspecified',
  inverted: false,
  transformer_nominal_current_a: null,
  transformer_ratio: null,
  notes: null,
  entities: []
})
const form = ref<SmartMeterMeasurementPointWrite>(emptyForm())

const phaseItems = ['L1', 'L2', 'L3', 'N']
const directionItems = [
  { title: 'Nicht angegeben', value: 'unspecified' },
  { title: 'Quelle → Ziel', value: 'source_to_target' },
  { title: 'Ziel → Quelle', value: 'target_to_source' }
]
const roleItems: Array<{ title: string; value: SmartMeterMeasurementEntityRole }> = [
  { title: 'Leistung', value: 'power' },
  { title: 'Strom', value: 'current' },
  { title: 'Spannung', value: 'voltage' },
  { title: 'Energie gesamt', value: 'energy' },
  { title: 'Energiebezug', value: 'energy_import' },
  { title: 'Einspeisung', value: 'energy_export' },
  { title: 'Frequenz', value: 'frequency' },
  { title: 'Leistungsfaktor', value: 'power_factor' },
  { title: 'Weitere Rolle', value: 'additional' }
]
const connectionItems = computed(() => connections.value.map((connection) => ({
  value: connection.id,
  title: connection.label || `${connection.source.name} → ${connection.target.name}`,
  subtitle: [connection.source.type_name, connection.target.type_name, connection.effective_phases.join(', ')]
    .filter(Boolean).join(' · ')
})))
const entityItems = computed(() => entities.value.map((entity) => ({
  value: entity.entity_id,
  title: entity.name || entity.entity_id,
  subtitle: [entity.entity_id, entity.state, entity.unit].filter(Boolean).join(' · ')
})))

async function load() {
  loading.value = true
  error.value = null
  try {
    const [pointRows, topology] = await Promise.all([
      smartMeterApi.measurementPoints(props.assetId),
      electricalApi.topology()
    ])
    points.value = pointRows
    connections.value = topology.connections.filter((item) => !item.deleted_at)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Messpunkte konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function loadEntities() {
  if (entities.value.length) return
  try {
    entities.value = await homeAssistantApi.allEntities({})
  } catch {
    // Manual entity IDs remain possible when Home Assistant is unavailable.
  }
}

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  editorOpen.value = true
  void loadEntities()
}

function openEdit(point: SmartMeterMeasurementPoint) {
  editingId.value = point.id
  form.value = {
    connection_id: point.connection_id,
    channel_name: point.channel_name,
    name: point.name,
    phase: point.phase,
    direction: point.direction,
    inverted: point.inverted,
    transformer_nominal_current_a: point.transformer_nominal_current_a,
    transformer_ratio: point.transformer_ratio,
    notes: point.notes,
    entities: point.entities.map((item) => ({ entity_id: item.entity_id, role: item.role }))
  }
  editorOpen.value = true
  void loadEntities()
}

function addEntity() {
  form.value.entities.push({ entity_id: '', role: 'additional' })
}

async function save() {
  if (!form.value.connection_id || !form.value.channel_name.trim() || !form.value.name.trim()) {
    error.value = 'Verkabelung, Kanal und Bezeichnung sind erforderlich.'
    return
  }
  if (form.value.entities.some((item) => !item.entity_id.trim())) {
    error.value = 'Leere Home-Assistant-Zuordnungen bitte entfernen oder ausfüllen.'
    return
  }
  saving.value = true
  error.value = null
  try {
    const payload: SmartMeterMeasurementPointWrite = {
      ...form.value,
      channel_name: form.value.channel_name.trim(),
      name: form.value.name.trim(),
      transformer_ratio: form.value.transformer_ratio?.trim() || null,
      notes: form.value.notes?.trim() || null,
      entities: form.value.entities.map((item) => ({
        role: item.role,
        entity_id: item.entity_id.trim()
      }))
    }
    if (editingId.value) {
      await smartMeterApi.updateMeasurementPoint(props.assetId, editingId.value, payload)
    } else {
      await smartMeterApi.createMeasurementPoint(props.assetId, payload)
    }
    editorOpen.value = false
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Messpunkt konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function remove() {
  if (!confirmDelete.value) return
  saving.value = true
  try {
    await smartMeterApi.removeMeasurementPoint(props.assetId, confirmDelete.value.id)
    confirmDelete.value = null
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Messpunkt konnte nicht entfernt werden.'
  } finally {
    saving.value = false
  }
}

function connectionText(point: SmartMeterMeasurementPoint) {
  return point.connection_label || `${point.connection_source_name} → ${point.connection_target_name}`
}

onMounted(() => void load())
</script>

<template>
  <v-card title="Smart-Meter-Messpunkte" prepend-icon="mdi-current-ac" class="mb-5">
    <template #append>
      <v-btn
        v-if="!readOnly"
        size="small"
        color="primary"
        prepend-icon="mdi-plus"
        @click="openCreate"
      >
        Messklemme
      </v-btn>
    </template>
    <v-card-text>
      <v-alert type="info" variant="tonal" density="compact" class="mb-4">
        CT- oder Stromwandlerklemmen messen eine vorhandene Leitung. Sie erzeugen keine neue stromführende Verbindung und können eigene Home-Assistant-Entitäten erhalten.
      </v-alert>
      <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
      <v-skeleton-loader v-if="loading" type="list-item-two-line@2" />
      <v-list v-else-if="points.length" lines="three">
        <v-list-item v-for="point in points" :key="point.id" prepend-icon="mdi-current-ac">
          <v-list-item-title>{{ point.channel_name }} · {{ point.name }}</v-list-item-title>
          <v-list-item-subtitle>
            {{ connectionText(point) }}
            <span v-if="point.phase"> · {{ point.phase }}</span>
            <span v-if="point.inverted"> · Richtung invertiert</span>
          </v-list-item-subtitle>
          <div v-if="point.entities.length" class="d-flex flex-wrap ga-1 mt-2">
            <v-chip v-for="entity in point.entities" :key="entity.id" size="x-small" variant="tonal">
              {{ roleItems.find((item) => item.value === entity.role)?.title || entity.role }}:
              {{ entity.entity_id }}
            </v-chip>
          </div>
          <template v-if="!readOnly" #append>
            <v-btn icon="mdi-pencil" variant="text" size="small" title="Messpunkt bearbeiten" @click="openEdit(point)" />
            <v-btn icon="mdi-delete-outline" variant="text" size="small" color="error" title="Messpunkt entfernen" @click="confirmDelete = point" />
          </template>
        </v-list-item>
      </v-list>
      <div v-else class="text-medium-emphasis">Noch keine Messklemmen dokumentiert.</div>
    </v-card-text>
  </v-card>

  <v-dialog v-model="editorOpen" max-width="860" persistent>
    <v-card :title="editingId ? 'Messklemme bearbeiten' : 'Messklemme anlegen'">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="3">
            <v-text-field v-model="form.channel_name" label="Kanal" placeholder="CT1" />
          </v-col>
          <v-col cols="12" md="5">
            <v-text-field v-model="form.name" label="Bezeichnung" placeholder="Hausanschluss L1" />
          </v-col>
          <v-col cols="12" md="4">
            <v-select v-model="form.phase" :items="phaseItems" label="Phase (optional)" clearable />
          </v-col>
          <v-col cols="12">
            <v-select
              v-model="form.connection_id"
              :items="connectionItems"
              label="Gemessene Verkabelung"
              item-title="title"
              item-value="value"
            >
              <template #item="{ props: itemProps, item }">
                <v-list-item v-bind="itemProps" :subtitle="item.raw.subtitle" />
              </template>
            </v-select>
          </v-col>
          <v-col cols="12" md="4">
            <v-select v-model="form.direction" :items="directionItems" label="Messrichtung" />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field v-model.number="form.transformer_nominal_current_a" label="Wandler-Nennstrom" type="number" suffix="A" clearable />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field v-model="form.transformer_ratio" label="Übersetzungsverhältnis" placeholder="100 A / 50 mA" clearable />
          </v-col>
          <v-col cols="12">
            <v-switch v-model="form.inverted" label="Messrichtung / Vorzeichen invertiert dokumentieren" color="primary" hide-details />
          </v-col>
          <v-col cols="12">
            <div class="d-flex align-center justify-space-between mb-2">
              <strong>Home-Assistant-Entitäten</strong>
              <v-btn size="small" variant="tonal" prepend-icon="mdi-plus" @click="addEntity">Entität</v-btn>
            </div>
            <v-row v-for="(binding, index) in form.entities" :key="index" dense>
              <v-col cols="12" md="4">
                <v-select v-model="binding.role" :items="roleItems" label="Rolle" />
              </v-col>
              <v-col cols="10" md="7">
                <v-combobox
                  v-model="binding.entity_id"
                  :items="entityItems"
                  item-title="title"
                  item-value="value"
                  label="Entity-ID"
                  placeholder="sensor.smart_meter_l1_power"
                />
              </v-col>
              <v-col cols="2" md="1" class="d-flex align-center">
                <v-btn icon="mdi-close" variant="text" color="error" title="Zuordnung entfernen" @click="form.entities.splice(index, 1)" />
              </v-col>
            </v-row>
          </v-col>
          <v-col cols="12">
            <v-textarea v-model="form.notes" label="Notiz (optional)" rows="2" />
          </v-col>
        </v-row>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="editorOpen = false">Abbrechen</v-btn>
        <v-btn color="primary" :loading="saving" @click="save">Speichern</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog :model-value="Boolean(confirmDelete)" max-width="480" @update:model-value="!$event && (confirmDelete = null)">
    <v-card title="Messpunkt entfernen?">
      <v-card-text>
        Die Messklemme „{{ confirmDelete?.channel_name }}“ wird aus der Dokumentation entfernt.
        Die elektrische Verkabelung selbst bleibt unverändert.
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="confirmDelete = null">Abbrechen</v-btn>
        <v-btn color="error" :loading="saving" @click="remove">Entfernen</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
