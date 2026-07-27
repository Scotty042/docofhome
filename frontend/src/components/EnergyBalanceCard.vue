<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { assetApi } from '../services/assetApi'
import { energyApi } from '../services/energyApi'
import type { Asset } from '../types/assets'
import type { ConsumptionMeter } from '../types/consumption'
import type {
  EnergyBalance,
  EnergyComponent,
  EnergyComponentType,
  EnergyComponentWrite,
  EnergyConfiguration,
  EnergyConfigurationWrite
} from '../types/energy'
import { energyComponentIcons, energyComponentLabels } from '../types/energy'

const props = defineProps<{ meters: ConsumptionMeter[] }>()

const loading = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)
const notice = ref<string | null>(null)
const configuration = ref<EnergyConfiguration | null>(null)
const configurationForm = ref<EnergyConfigurationWrite>(emptyConfiguration())
const components = ref<EnergyComponent[]>([])
const assets = ref<Asset[]>([])
const balance = ref<EnergyBalance | null>(null)
const months = ref(12)
const dialog = ref(false)
const editing = ref<EnergyComponent | null>(null)
const componentForm = ref<EnergyComponentWrite>(emptyComponent())

const importMeters = computed(() => props.meters.filter((item) => item.meter_type === 'electricity_grid'))
const pvMeters = computed(() => props.meters.filter((item) => item.meter_type === 'electricity_pv'))
const exportMeters = computed(() => props.meters.filter((item) => item.meter_type === 'electricity_feed_in'))
const latest = computed(() => [...(balance.value?.periods ?? [])].reverse().find((item) => item.house_consumption_kwh !== null) ?? null)
const componentTypeItems = (
  Object.entries(energyComponentLabels) as Array<[EnergyComponentType, string]>
).map(([value, title]) => ({ value, title }))

function emptyConfiguration(): EnergyConfigurationWrite {
  return {
    grid_connection_name: null,
    grid_operator: null,
    energy_supplier: null,
    metering_point_id: null,
    connection_capacity_kw: null,
    grid_import_meter_id: null,
    pv_generation_meter_id: null,
    grid_export_meter_id: null,
    notes: null
  }
}

function emptyComponent(): EnergyComponentWrite {
  return {
    component_type: 'pv_source',
    name: '',
    asset_id: null,
    manufacturer: null,
    model: null,
    serial_number: null,
    rated_power_kw: null,
    capacity_kwh: null,
    sort_order: 100,
    notes: null
  }
}

function format(value: number | null | undefined, suffix = '', decimals = 1) {
  if (value === null || value === undefined) return '–'
  return `${new Intl.NumberFormat('de-DE', { maximumFractionDigits: decimals }).format(value)}${suffix}`
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const [config, componentRows, balanceData, assetRows] = await Promise.all([
      energyApi.configuration(),
      energyApi.components(),
      energyApi.balance(months.value),
      assetApi.allAssets()
    ])
    configuration.value = config
    configurationForm.value = {
      grid_connection_name: config.grid_connection_name,
      grid_operator: config.grid_operator,
      energy_supplier: config.energy_supplier,
      metering_point_id: config.metering_point_id,
      connection_capacity_kw: config.connection_capacity_kw,
      grid_import_meter_id: config.grid_import_meter_id,
      pv_generation_meter_id: config.pv_generation_meter_id,
      grid_export_meter_id: config.grid_export_meter_id,
      notes: config.notes
    }
    components.value = componentRows
    balance.value = balanceData
    assets.value = assetRows.filter((asset) => asset.status !== 'retired')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Energiebilanz konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function saveConfiguration() {
  saving.value = true
  error.value = null
  try {
    configuration.value = await energyApi.updateConfiguration(configurationForm.value)
    balance.value = await energyApi.balance(months.value)
    notice.value = 'Energieanschluss und Zählerzuordnung wurden gespeichert.'
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Energiekonfiguration konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

function openComponent(component?: EnergyComponent) {
  editing.value = component ?? null
  componentForm.value = component ? {
    component_type: component.component_type,
    name: component.name,
    asset_id: component.asset_id,
    manufacturer: component.manufacturer,
    model: component.model,
    serial_number: component.serial_number,
    rated_power_kw: component.rated_power_kw,
    capacity_kwh: component.capacity_kwh,
    sort_order: component.sort_order,
    notes: component.notes
  } : emptyComponent()
  dialog.value = true
}

async function saveComponent() {
  saving.value = true
  error.value = null
  try {
    if (editing.value) await energyApi.updateComponent(editing.value.id, componentForm.value)
    else await energyApi.createComponent(componentForm.value)
    dialog.value = false
    components.value = await energyApi.components()
    notice.value = 'Energiekomponente wurde gespeichert.'
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Energiekomponente konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function archiveComponent(component: EnergyComponent) {
  if (!confirm(`„${component.name}“ archivieren?`)) return
  try {
    await energyApi.removeComponent(component.id)
    components.value = await energyApi.components()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Energiekomponente konnte nicht archiviert werden.'
  }
}

watch(months, async () => {
  try { balance.value = await energyApi.balance(months.value) }
  catch (reason) { error.value = reason instanceof Error ? reason.message : 'Energiebilanz konnte nicht geladen werden.' }
})

watch(() => componentForm.value.component_type, (componentType) => {
  if (componentType !== 'storage') componentForm.value.capacity_kwh = null
})

onMounted(() => void load())
</script>

<template>
  <div>
    <v-alert v-if="error" type="error" closable class="mb-4" @click:close="error = null">{{ error }}</v-alert>
    <v-alert v-if="notice" type="success" closable class="mb-4" @click:close="notice = null">{{ notice }}</v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <v-alert type="info" variant="tonal" class="mb-4" icon="mdi-solar-power-variant">
      Hausverbrauch = Netzbezug + PV-Erzeugung − Netzeinspeisung. Eigenverbrauch,
      Autarkiegrad und Eigenverbrauchsquote werden daraus je Monat berechnet.
    </v-alert>

    <v-row class="mb-2">
      <v-col cols="6" md="3"><v-card title="Hausverbrauch"><v-card-text class="text-h5">{{ format(latest?.house_consumption_kwh, ' kWh') }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Eigenverbrauch"><v-card-text class="text-h5">{{ format(latest?.self_consumption_kwh, ' kWh') }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Autarkiegrad"><v-card-text class="text-h5">{{ format(latest?.autonomy_percent, ' %') }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Eigenverbrauchsquote"><v-card-text class="text-h5">{{ format(latest?.self_consumption_rate_percent, ' %') }}</v-card-text></v-card></v-col>
    </v-row>

    <v-card class="mb-4" title="Netzanschluss und Bilanzzähler" prepend-icon="mdi-transmission-tower">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="6"><v-text-field v-model="configurationForm.grid_connection_name" label="Netzanschluss (optional)" hint="Bezeichnung des dokumentierten Hausanschlusses, z. B. Hausanschluss Hauptgebäude." persistent-hint clearable /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="configurationForm.metering_point_id" label="Zählpunkt / Marktlokation (optional)" hint="Kennung aus Vertrag, Rechnung oder Unterlagen des Netzbetreibers." persistent-hint clearable /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="configurationForm.grid_operator" label="Netzbetreiber (optional)" hint="Betreiber des örtlichen Stromnetzes, nicht der Stromlieferant." persistent-hint clearable /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="configurationForm.energy_supplier" label="Energieversorger (optional)" hint="Vertragspartner für den Strombezug, nicht der Netzbetreiber." persistent-hint clearable /></v-col>
          <v-col cols="12" md="4"><v-text-field v-model.number="configurationForm.connection_capacity_kw" type="number" min="0" suffix="kW" label="Anschlussleistung (optional)" hint="Maximale Anschlussleistung in kW, z. B. 30 kW." persistent-hint clearable /></v-col>
          <v-col cols="12" md="4"><v-select v-model="configurationForm.grid_import_meter_id" :items="importMeters" item-title="name" item-value="id" label="Netzbezug (optional)" hint="Zähler für die aus dem öffentlichen Netz bezogene Energie (typisch OBIS 1.8.0)." persistent-hint clearable /></v-col>
          <v-col cols="12" md="4"><v-select v-model="configurationForm.pv_generation_meter_id" :items="pvMeters" item-title="name" item-value="id" label="PV-Erzeugung (optional)" hint="Zähler für die gesamte von der PV-Anlage erzeugte Energie." persistent-hint clearable /></v-col>
          <v-col cols="12" md="4"><v-select v-model="configurationForm.grid_export_meter_id" :items="exportMeters" item-title="name" item-value="id" label="Netzeinspeisung (optional)" hint="Zähler für die ins öffentliche Netz eingespeiste Energie (typisch OBIS 2.8.0)." persistent-hint clearable /></v-col>
          <v-col cols="12"><v-textarea v-model="configurationForm.notes" label="Notizen" rows="2" clearable /></v-col>
        </v-row>
        <v-alert v-if="!configuration?.complete_for_balance" type="warning" variant="tonal" density="compact" class="mb-3">
          Für eine vollständige Bilanz müssen Netzbezug, PV-Erzeugung und Netzeinspeisung zugeordnet sein.
        </v-alert>
        <v-btn color="primary" :loading="saving" @click="saveConfiguration">Konfiguration speichern</v-btn>
      </v-card-text>
    </v-card>

    <v-card class="mb-4" prepend-icon="mdi-solar-power-variant">
      <v-card-title class="d-flex flex-wrap align-center ga-2">Energiequellen, Wechselrichter und Speicher<v-spacer /><v-btn color="primary" prepend-icon="mdi-plus" @click="openComponent()">Komponente</v-btn></v-card-title>
      <v-card-text>
        <v-row v-if="components.length">
          <v-col v-for="component in components" :key="component.id" cols="12" md="6" lg="4">
            <v-card variant="outlined" height="100%">
              <v-card-title class="d-flex align-center ga-2"><v-icon :icon="energyComponentIcons[component.component_type]" />{{ component.name }}</v-card-title>
              <v-card-subtitle>{{ energyComponentLabels[component.component_type] }}</v-card-subtitle>
              <v-card-text>
                <div v-if="component.manufacturer || component.model">{{ [component.manufacturer, component.model].filter(Boolean).join(' · ') }}</div>
                <div v-if="component.rated_power_kw">Leistung: {{ format(component.rated_power_kw, ' kW') }}</div>
                <div v-if="component.capacity_kwh">Kapazität: {{ format(component.capacity_kwh, ' kWh') }}</div>
                <div v-if="component.asset_name" class="text-medium-emphasis">Asset: {{ component.asset_name }}</div>
              </v-card-text>
              <v-card-actions><v-btn variant="text" prepend-icon="mdi-pencil" @click="openComponent(component)">Bearbeiten</v-btn><v-spacer /><v-btn icon="mdi-archive-outline" color="error" variant="text" @click="archiveComponent(component)" /></v-card-actions>
            </v-card>
          </v-col>
        </v-row>
        <v-empty-state v-else icon="mdi-solar-power-variant" title="Noch keine Energiekomponenten" text="Lege PV-Quellen, Wechselrichter und Speicher einzeln an." />
        <v-btn class="mt-3" variant="tonal" prepend-icon="mdi-source-branch" to="/electrical/topology">In Elektro-Topologie öffnen</v-btn>
      </v-card-text>
    </v-card>

    <v-card title="Monatliche Energiebilanz" prepend-icon="mdi-chart-line">
      <v-card-title class="d-flex align-center ga-2"><v-spacer /><v-select v-model="months" :items="[6, 12, 24, 36]" label="Monate" density="compact" hide-details max-width="150" /></v-card-title>
      <v-card-text>
        <div class="table-scroll"><v-table density="compact"><thead><tr><th>Monat</th><th>Netzbezug</th><th>PV</th><th>Einspeisung</th><th>Hausverbrauch</th><th>Eigenverbrauch</th><th>Autarkie</th><th>Eigenverbrauchsquote</th></tr></thead><tbody>
          <tr v-for="period in balance?.periods ?? []" :key="period.period_start">
            <td>{{ period.label }} <v-chip v-if="period.incomplete" size="x-small" color="warning" variant="tonal">unvollständig</v-chip></td>
            <td>{{ format(period.grid_import_kwh, ' kWh') }}</td><td>{{ format(period.pv_generation_kwh, ' kWh') }}</td><td>{{ format(period.grid_export_kwh, ' kWh') }}</td>
            <td>{{ format(period.house_consumption_kwh, ' kWh') }}</td><td>{{ format(period.self_consumption_kwh, ' kWh') }}</td><td>{{ format(period.autonomy_percent, ' %') }}</td><td>{{ format(period.self_consumption_rate_percent, ' %') }}</td>
          </tr>
        </tbody></v-table></div>
      </v-card-text>
    </v-card>

    <v-dialog v-model="dialog" max-width="720">
      <v-card :title="editing ? 'Energiekomponente bearbeiten' : 'Energiekomponente anlegen'">
        <v-card-text><v-row>
          <v-col cols="12" md="5"><v-select v-model="componentForm.component_type" :items="componentTypeItems" label="Typ" /></v-col>
          <v-col cols="12" md="7"><v-text-field v-model="componentForm.name" label="Name" autofocus /></v-col>
          <v-col cols="12"><v-autocomplete v-model="componentForm.asset_id" :items="assets" item-title="name" item-value="id" label="Verknüpftes Asset" hint="Optional: verbindet die Energiekomponente mit Inventar und Elektro-Topologie." persistent-hint clearable /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="componentForm.manufacturer" label="Hersteller" clearable /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="componentForm.model" label="Modell" clearable /></v-col>
          <v-col cols="12" md="6"><v-text-field v-model="componentForm.serial_number" label="Seriennummer" clearable /></v-col>
          <v-col cols="12" md="3"><v-text-field v-model.number="componentForm.rated_power_kw" type="number" suffix="kW" label="Leistung" clearable /></v-col>
          <v-col v-if="componentForm.component_type === 'storage'" cols="12" md="3"><v-text-field v-model.number="componentForm.capacity_kwh" type="number" suffix="kWh" label="Kapazität" clearable /></v-col>
          <v-col cols="12"><v-textarea v-model="componentForm.notes" label="Notizen" rows="3" clearable /></v-col>
        </v-row></v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="dialog = false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="saveComponent">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.table-scroll { overflow-x: auto; }
</style>
