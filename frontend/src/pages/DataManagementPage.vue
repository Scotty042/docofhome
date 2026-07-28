<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { releaseApi } from '../services/releaseApi'
import type { AuditEvent, ImportPreview, ImportResult } from '../types/release'

const tab = ref('export')
const file = ref<File | null>(null)
const preview = ref<ImportPreview | null>(null)
const result = ref<ImportResult | null>(null)
const strategy = ref<'fail' | 'skip'>('fail')
const audit = ref<AuditEvent[]>([])
const selectedEvent = ref<AuditEvent | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const historySearch = ref('')
const historyAction = ref('')
const historyObjectType = ref('')


const objectTypeLabels: Record<string, string> = {
  assets: 'Asset', locations: 'Bereich oder Raum', asset_types: 'Asset-Typ', products: 'Produkt',
  labels: 'Label', relationships: 'Asset-Beziehung', electrical_distributions: 'Elektroverteilung',
  electrical_circuits: 'Stromkreis', electrical_protective_devices: 'Schutzgerät',
  electrical_connections: 'Elektrische Verbindung', network_devices: 'Netzwerkgerät',
  network_interfaces: 'Netzwerkschnittstelle', network_addresses: 'IP-Adresse',
  network_segments: 'IP-Netz', network_connections: 'Netzwerkverbindung',
  consumption_meters: 'Verbrauchszähler', consumption_readings: 'Zählerstand',
  consumption_notes: 'Verbrauchsnotiz', work_items: 'Wartung oder Aufgabe',
  work_item_events: 'Aufgabenereignis', wiki_pages: 'Wiki-Seite', domain_notes: 'Notiz',
  document_links: 'Dokumentverknüpfung', immich_asset_links: 'Bildverknüpfung',
  home_assistant_asset_links: 'Home-Assistant-Verknüpfung', service_workloads: 'Dienst oder Container',
  dashboard_settings: 'Dashboard-Einstellung', system_settings: 'Systemeinstellung',
  application_settings: 'Anwendungseinstellung', quality_runs: 'Qualitätsprüfung', quality_issues: 'Qualitätshinweis'
}

const fieldLabels: Record<string, string> = {
  name: 'Name', title: 'Titel', description: 'Beschreibung', status: 'Status', hostname: 'Hostname',
  role: 'Rolle', location_id: 'Raum/Bereich', asset_type_id: 'Asset-Typ', product_id: 'Produkt',
  inventory_number: 'Inventarnummer', serial_number: 'Seriennummer', notes: 'Notizen',
  parent_id: 'Übergeordneter Bereich', location_type: 'Bereichstyp', short_name: 'Kurzname',
  sort_order: 'Sortierung', enabled: 'Aktiviert', visible: 'Sichtbar', due_at: 'Fälligkeit',
  completed_at: 'Abgeschlossen am', priority: 'Priorität', mac_address: 'MAC-Adresse',
  speed_mbps: 'Geschwindigkeit', interface_type: 'Schnittstellentyp', address: 'IP-Adresse',
  assignment_type: 'Adresszuweisung', cidr: 'Netz/CIDR', gateway: 'Gateway', vlan_id: 'VLAN-ID',
  unit: 'Einheit', meter_type: 'Zählertyp', reading_value: 'Zählerstand', value: 'Wert',
  deleted_at: 'Archivierung', layout_json: 'Dashboard-Anordnung', asset_id: 'Asset',
  source_asset_id: 'Quell-Asset', target_asset_id: 'Ziel-Asset', host_asset_id: 'Host-Asset',
  network_device_id: 'Netzwerkgerät', interface_id: 'Schnittstelle',
  source_interface_id: 'Quell-Schnittstelle', target_interface_id: 'Ziel-Schnittstelle',
  segment_id: 'IP-Netz', meter_id: 'Verbrauchszähler', parent_meter_id: 'Übergeordneter Zähler',
  work_item_id: 'Aufgabe', distribution_id: 'Verteilung', parent_distribution_id: 'Übergeordnete Verteilung',
  circuit_id: 'Stromkreis', protective_device_id: 'Historisches Schutzgerät',
  protective_device_asset_id: 'DIN-Schutzgerät', target_type: 'Bezugsart', target_id: 'Bezogenes Objekt'
}

const fieldValueLabels: Record<string, Record<string, string>> = {
  status: {
    active: 'Aktiv', inactive: 'Inaktiv', maintenance: 'Wartung', retired: 'Ausgemustert',
    open: 'Offen', completed: 'Abgeschlossen', cancelled: 'Abgebrochen',
    running: 'Läuft', stopped: 'Gestoppt', planned: 'Geplant', unknown: 'Unbekannt'
  },
  role: {
    router: 'Router', firewall: 'Firewall', switch: 'Switch', access_point: 'Access Point',
    server: 'Server', nas: 'NAS', client: 'Client', iot: 'IoT-Gerät', printer: 'Drucker',
    controller: 'Controller', other: 'Sonstiges'
  },
  location_type: { building: 'Gebäude', floor: 'Etage', room: 'Raum', outdoor: 'Außenbereich' },
  interface_type: {
    ethernet: 'Ethernet', wifi: 'WLAN', fiber: 'Glasfaser', virtual: 'Virtuell',
    cellular: 'Mobilfunk', other: 'Sonstiges'
  },
  assignment_type: {
    static: 'Statisch', dhcp: 'DHCP', reservation: 'DHCP-Reservierung',
    link_local: 'Link-Local', unknown: 'Unbekannt'
  },
  priority: { low: 'Niedrig', normal: 'Normal', high: 'Hoch' },
  meter_type: {
    water: 'Wasser', electricity_grid: 'Netzstrom', electricity_pv: 'Photovoltaik', electricity_feed_in: 'Netzeinspeisung',
    gas: 'Gas', heat: 'Wärme', oil: 'Öl', other: 'Sonstiges'
  },
  action: { create: 'Neu angelegt', update: 'Geändert', archive: 'Archiviert', restore: 'Wiederhergestellt', delete: 'Gelöscht' }
}

const actionItems = [
  { value: '', title: 'Alle Aktionen' },
  { value: 'create', title: 'Neu angelegt' },
  { value: 'update', title: 'Geändert' },
  { value: 'archive', title: 'Archiviert' },
  { value: 'restore', title: 'Wiederhergestellt' },
  { value: 'delete', title: 'Gelöscht' }
]
const objectTypeItems = computed(() => [
  { value: '', title: 'Alle Objektarten' },
  ...Array.from(new Set(audit.value.map((event) => event.object_type)))
    .sort((a, b) => objectTypeLabel(a).localeCompare(objectTypeLabel(b), 'de'))
    .map((value) => ({ value, title: objectTypeLabel(value) }))
])
const filteredAudit = computed(() => {
  const query = historySearch.value.trim().toLocaleLowerCase('de-DE')
  return audit.value.filter((event) => {
    if (historyAction.value && event.action !== historyAction.value) return false
    if (historyObjectType.value && event.object_type !== historyObjectType.value) return false
    if (!query) return true
    return [event.object_label, objectTypeLabel(event.object_type), actionLabel(event.action), ...eventChanges(event).map((item) => `${item.label} ${formatHistoryValue(item.from, item.key)} ${formatHistoryValue(item.to, item.key)}`)]
      .filter(Boolean).join(' ').toLocaleLowerCase('de-DE').includes(query)
  })
})

function objectTypeLabel(value: string) {
  return objectTypeLabels[value] ?? value.replaceAll('_', ' ')
}

function actionLabel(value: string) {
  return ({ create: 'Neu angelegt', update: 'Geändert', archive: 'Archiviert', restore: 'Wiederhergestellt', delete: 'Gelöscht' } as Record<string, string>)[value] ?? value
}

function actionColor(value: string) {
  return ({ create: 'success', update: 'primary', archive: 'warning', restore: 'info', delete: 'error' } as Record<string, string>)[value]
}

function actionIcon(value: string) {
  return ({ create: 'mdi-plus', update: 'mdi-pencil', archive: 'mdi-archive-outline', restore: 'mdi-restore', delete: 'mdi-delete-outline' } as Record<string, string>)[value] ?? 'mdi-history'
}

function fieldLabel(value: string) {
  return fieldLabels[value] ?? value.replaceAll('_', ' ')
}

function formatHistoryValue(value: unknown, field = ''): string {
  if (value === '[redacted]') return 'Geschützter Wert'
  if (value === null || value === undefined || value === '') return 'leer'
  if (typeof value === 'boolean') return value ? 'Ja' : 'Nein'
  if (Array.isArray(value)) {
    return value.length ? value.map((item) => formatHistoryValue(item, field)).join(', ') : 'leer'
  }
  if (typeof value === 'object') return JSON.stringify(value)
  const text = String(value)
  const translated = fieldValueLabels[field]?.[text]
  if (translated) return translated
  if (/^\d{4}-\d{2}-\d{2}T/.test(text)) {
    const date = new Date(text)
    if (!Number.isNaN(date.getTime())) return date.toLocaleString('de-DE')
  }
  return text
}

function eventChanges(event: AuditEvent) {
  const ignored = new Set(['id', 'created_at', 'updated_at'])
  return Object.entries(event.display_change ?? event.change)
    .filter(([key]) => !ignored.has(key))
    .map(([key, raw]) => {
      if (raw && typeof raw === 'object' && !Array.isArray(raw) && ('from' in raw || 'to' in raw)) {
        const values = raw as { from?: unknown; to?: unknown }
        return { key, label: fieldLabel(key), from: values.from, to: values.to }
      }
      return { key, label: fieldLabel(key), from: null, to: raw }
    })
}

function eventObjectLabel(event: AuditEvent) {
  return event.object_label || `${objectTypeLabel(event.object_type)} ${event.object_id.slice(0, 8)}`
}

const csvModules = [
  'assets',
  'locations',
  'work_items',
  'network_devices',
  'consumption_meters',
  'consumption_readings',
  'service_workloads'
]

function pickFile(value: File | File[] | null) {
  file.value = Array.isArray(value) ? value[0] ?? null : value
  preview.value = null
  result.value = null
}

async function previewFile() {
  if (!file.value) return
  loading.value = true
  error.value = null
  try {
    preview.value = await releaseApi.previewImport(file.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Importvorschau fehlgeschlagen.'
  } finally {
    loading.value = false
  }
}

async function applyFile() {
  if (!file.value || !preview.value) return
  loading.value = true
  error.value = null
  try {
    result.value = await releaseApi.applyImport(file.value, strategy.value)
    await loadAudit()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Import fehlgeschlagen.'
  } finally {
    loading.value = false
  }
}

async function loadAudit() {
  audit.value = await releaseApi.audit('?limit=300')
}

onMounted(loadAudit)
</script>

<template>
  <v-container fluid class="pa-4 pa-md-6">
    <h1 class="text-h4 font-weight-bold">Daten & Änderungshistorie</h1>
    <p class="text-medium-emphasis mb-5">
      Portabler Export, transaktionaler Import und unveränderliche Historie ohne Secrets.
    </p>

    <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>
    <v-tabs v-model="tab" class="mb-4">
      <v-tab value="export">Export</v-tab>
      <v-tab value="import">Import</v-tab>
      <v-tab value="history">Änderungshistorie</v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <v-window-item value="export">
        <v-card title="Vollständiger DocOfHome-Export" prepend-icon="mdi-database-export-outline">
          <v-card-text>
            <v-alert type="info" variant="tonal" class="mb-4">
              Zugangsdaten, Tokens, API-Keys, interne Integrations-URLs und Kontonamen werden
              ausdrücklich nicht exportiert. Stabile IDs und Beziehungen bleiben erhalten.
            </v-alert>
            <v-btn
              color="primary"
              prepend-icon="mdi-download"
              :href="releaseApi.exportUrl"
              download
            >
              JSON-Export herunterladen
            </v-btn>
            <v-divider class="my-5" />
            <div class="text-subtitle-1 font-weight-bold mb-2">CSV je Modul</div>
            <div class="d-flex flex-wrap ga-2">
              <v-btn
                v-for="module in csvModules"
                :key="module"
                variant="tonal"
                prepend-icon="mdi-file-delimited-outline"
                :href="releaseApi.csvExportUrl(module)"
                download
              >
                {{ module }}
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="import">
        <v-card title="Import mit Vorschau" prepend-icon="mdi-database-import-outline">
          <v-card-text>
            <v-file-input
              label="DocOfHome-JSON-Export"
              accept=".json,application/json"
              @update:model-value="pickFile"
            />
            <v-radio-group v-model="strategy" inline label="Konfliktstrategie">
              <v-radio value="fail" label="Bei Konflikt vollständig abbrechen" />
              <v-radio value="skip" label="Konflikte überspringen, nie überschreiben" />
            </v-radio-group>
            <div class="d-flex ga-2 mb-4">
              <v-btn :disabled="!file" :loading="loading" @click="previewFile">Vorschau</v-btn>
              <v-btn
                color="primary"
                :disabled="!preview"
                :loading="loading"
                @click="applyFile"
              >
                Transaktional importieren
              </v-btn>
            </div>
            <v-sheet v-if="preview" border rounded class="pa-4">
              <strong>{{ preview.format }} · Schema {{ preview.export_version ?? 'unbekannt' }}</strong>
              <div class="mt-2">
                {{ Object.values(preview.record_counts).reduce((sum, value) => sum + value, 0) }}
                Datensätze in {{ Object.keys(preview.record_counts).length }} Modulen.
              </div>
              <v-alert v-if="preview.conflicts.length" type="warning" class="mt-3">
                {{ preview.conflicts.length }} Konflikte erkannt. Es wird niemals still überschrieben.
              </v-alert>
              <v-alert
                v-for="warning in preview.warnings"
                :key="warning"
                type="info"
                density="compact"
                class="mt-2"
              >
                {{ warning }}
              </v-alert>
            </v-sheet>
            <v-alert v-if="result" type="success" class="mt-4">
              {{ result.created }} Datensätze angelegt, {{ result.skipped }} übersprungen,
              {{ result.conflicts }} Konflikte. Der Import wurde vollständig abgeschlossen.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-window-item>

      <v-window-item value="history">
        <v-card title="Verständliche Änderungshistorie" prepend-icon="mdi-history">
          <v-card-text>
            <v-alert type="info" variant="tonal" class="mb-4">
              Technische IDs und RAW-Daten sind nur noch in der Detailansicht sichtbar. Zugangsdaten, Tokens und Kennwörter bleiben ausgeblendet.
            </v-alert>
            <v-row dense class="mb-3">
              <v-col cols="12" md="6">
                <v-text-field v-model="historySearch" label="Historie durchsuchen" prepend-inner-icon="mdi-magnify" clearable hide-details />
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-select v-model="historyObjectType" :items="objectTypeItems" label="Objektart" hide-details />
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-select v-model="historyAction" :items="actionItems" label="Aktion" hide-details />
              </v-col>
            </v-row>

            <v-card v-for="event in filteredAudit" :key="event.id" variant="outlined" class="mb-3">
              <v-card-title class="d-flex flex-wrap align-center ga-2">
                <v-icon :icon="actionIcon(event.action)" :color="actionColor(event.action)" />
                <span>{{ eventObjectLabel(event) }}</span>
                <v-chip size="small" :color="actionColor(event.action)" variant="tonal">{{ actionLabel(event.action) }}</v-chip>
              </v-card-title>
              <v-card-subtitle>
                {{ objectTypeLabel(event.object_type) }} · {{ new Date(event.created_at).toLocaleString('de-DE') }}
              </v-card-subtitle>
              <v-card-text>
                <div v-if="eventChanges(event).length" class="change-list">
                  <div v-for="change in eventChanges(event).slice(0, 4)" :key="change.key" class="change-row">
                    <strong>{{ change.label }}</strong>
                    <span class="old-value">{{ formatHistoryValue(change.from, change.key) }}</span>
                    <v-icon icon="mdi-arrow-right" size="small" />
                    <span class="new-value">{{ formatHistoryValue(change.to, change.key) }}</span>
                  </div>
                  <div v-if="eventChanges(event).length > 4" class="text-caption text-medium-emphasis mt-2">
                    + {{ eventChanges(event).length - 4 }} weitere Änderungen
                  </div>
                </div>
                <span v-else class="text-medium-emphasis">Keine fachlichen Felder im Ereignis enthalten.</span>
              </v-card-text>
              <v-card-actions>
                <v-btn v-if="event.object_route" variant="text" prepend-icon="mdi-open-in-new" :to="event.object_route">Objekt öffnen</v-btn>
                <v-spacer />
                <v-btn variant="text" prepend-icon="mdi-eye-outline" @click="selectedEvent = event">Alle Details</v-btn>
              </v-card-actions>
            </v-card>
            <v-empty-state
              v-if="filteredAudit.length === 0"
              icon="mdi-history"
              :title="audit.length ? 'Keine passenden Änderungen' : 'Noch keine Änderungen protokolliert'"
            />
          </v-card-text>
        </v-card>
      </v-window-item>
    </v-window>

    <v-dialog :model-value="selectedEvent !== null" max-width="820" @update:model-value="selectedEvent = null">
      <v-card v-if="selectedEvent" :title="eventObjectLabel(selectedEvent)" :prepend-icon="actionIcon(selectedEvent.action)">
        <v-card-subtitle>
          {{ actionLabel(selectedEvent.action) }} · {{ objectTypeLabel(selectedEvent.object_type) }} · {{ new Date(selectedEvent.created_at).toLocaleString('de-DE') }}
        </v-card-subtitle>
        <v-card-text>
          <v-table density="compact">
            <thead><tr><th>Feld</th><th>Vorher</th><th>Nachher</th></tr></thead>
            <tbody>
              <tr v-for="change in eventChanges(selectedEvent)" :key="change.key">
                <td><strong>{{ change.label }}</strong></td>
                <td class="old-value">{{ formatHistoryValue(change.from, change.key) }}</td>
                <td class="new-value">{{ formatHistoryValue(change.to, change.key) }}</td>
              </tr>
            </tbody>
          </v-table>
          <v-expansion-panels class="mt-4">
            <v-expansion-panel title="Technische Details und RAW-Daten">
              <v-expansion-panel-text>
                <div class="text-caption mb-2">Objekt-ID: {{ selectedEvent.object_id }}</div>
                <pre class="history-detail">{{ JSON.stringify(selectedEvent.change, null, 2) }}</pre>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        <v-card-actions>
          <v-btn v-if="selectedEvent.object_route" variant="text" prepend-icon="mdi-open-in-new" :to="selectedEvent.object_route" @click="selectedEvent = null">Objekt öffnen</v-btn>
          <v-spacer /><v-btn @click="selectedEvent = null">Schließen</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.change-list { display: grid; gap: 0.55rem; }
.change-row { display: grid; grid-template-columns: minmax(130px, 0.8fr) minmax(100px, 1fr) auto minmax(100px, 1fr); gap: 0.65rem; align-items: center; }
.old-value { color: rgb(var(--v-theme-secondary)); overflow-wrap: anywhere; }
.new-value { color: rgb(var(--v-theme-primary)); font-weight: 500; overflow-wrap: anywhere; }

.history-detail {
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 700px) {
  .change-row { grid-template-columns: 1fr; gap: 0.15rem; padding-block: 0.5rem; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
  .change-row .v-icon { transform: rotate(90deg); }
}
</style>
