<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { assetApi } from '../services/assetApi'
import { electricalApi } from '../services/electricalApi'
import { consumptionApi } from '../services/consumptionApi'
import { knowledgeApi } from '../services/knowledgeApi'
import { protectiveDeviceLabels } from '../services/electricalPresentation'
import type { Asset, Page } from '../types/assets'
import type { ConsumptionMeter } from '../types/consumption'
import { consumptionMeterTypeLabels } from '../types/consumption'
import type { Distribution, ProtectiveDevice } from '../types/electrical'
import type { WikiPageRead } from '../types/knowledge'

const tab = ref<'assets' | 'distributions' | 'devices' | 'wiki' | 'consumption'>('devices')
const assets = ref<Asset[]>([])
const allDistributions = ref<Distribution[]>([])
const devices = ref<ProtectiveDevice[]>([])
const wikiPages = ref<WikiPageRead[]>([])
const consumptionMeters = ref<ConsumptionMeter[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const distributions = computed(() => allDistributions.value.filter((item) => item.deleted_at))
const distributionById = computed(() => new Map(
  allDistributions.value.map((distribution) => [distribution.id, distribution])
))

async function loadAll<T>(loader: (page: number) => Promise<Page<T>>): Promise<T[]> {
  const first = await loader(1)
  const items = [...first.items]
  for (let page = 2; page <= first.pages; page += 1) {
    items.push(...(await loader(page)).items)
  }
  return items
}

function distributionLocation(distributionId: string) {
  const distribution = distributionById.value.get(distributionId)
  if (!distribution) return '/electrical'
  return distribution.deleted_at
    ? { path: `/electrical/distributions/${distribution.id}`, query: { archived: '1' } }
    : `/electrical/distributions/${distribution.id}`
}

onMounted(async () => {
  try {
    const [allAssets, loadedDistributions, allDevices, allWikiPages, loadedConsumptionMeters] = await Promise.all([
      loadAll((page) => assetApi.list({ page, page_size: 100, include_deleted: true })),
      loadAll((page) => electricalApi.listDistributions({
        page, page_size: 100, include_deleted: true
      })),
      loadAll((page) => electricalApi.listProtectiveDevices({
        page, page_size: 100, include_deleted: true
      })),
      knowledgeApi.wikiPages(undefined, true),
      consumptionApi.meters({ include_archived: true })
    ])
    assets.value = allAssets.filter((item) => item.deleted_at)
    allDistributions.value = loadedDistributions
    devices.value = allDevices.filter((item) => item.deleted_at)
    wikiPages.value = allWikiPages.filter((item) => item.archived)
    consumptionMeters.value = loadedConsumptionMeters.filter((item) => item.archived)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Archiv konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <v-container class="archive-container pa-4 pa-sm-6" fluid>
    <div class="mb-5">
      <h1>Archiv und Historie</h1>
      <p class="text-medium-emphasis mb-0">
        Archivierte Datensätze bleiben dauerhaft nachvollziehbar, werden aber nicht mehr in
        aktiven Auswahlen verwendet.
      </p>
    </div>

    <v-alert type="info" variant="tonal" class="mb-5">
      Das Archiv ist bewusst schreibgeschützt. Eine Wiederherstellung folgt erst mit Prüfungen
      auf belegte Assets, Codes, Modulpositionen und andere Konflikte.
    </v-alert>
    <v-alert v-if="error" type="error" variant="tonal" class="mb-5">{{ error }}</v-alert>
    <v-skeleton-loader v-if="loading" type="heading, table" />

    <v-card v-else rounded="xl">
      <v-tabs v-model="tab" color="primary" grow>
        <v-tab value="assets" prepend-icon="mdi-archive-outline">
          Assets ({{ assets.length }})
        </v-tab>
        <v-tab value="distributions" prepend-icon="mdi-electric-switch">
          Verteilungen ({{ distributions.length }})
        </v-tab>
        <v-tab value="devices" prepend-icon="mdi-shield-outline">
          Schutzgeräte ({{ devices.length }})
        </v-tab>
        <v-tab value="wiki" prepend-icon="mdi-book-open-page-variant">
          Wiki ({{ wikiPages.length }})
        </v-tab>
        <v-tab value="consumption" prepend-icon="mdi-chart-line">
          Zähler ({{ consumptionMeters.length }})
        </v-tab>
      </v-tabs>
      <v-divider />

      <v-window v-model="tab">
        <v-window-item value="assets">
          <v-card-text v-if="assets.length === 0" class="text-center py-10">
            Keine archivierten Assets vorhanden.
          </v-card-text>
          <div v-else class="table-scroll">
            <v-table hover>
              <thead><tr><th>Name</th><th>Typ</th><th>Ort</th><th>Archiviert</th><th /></tr></thead>
              <tbody>
                <tr v-for="asset in assets" :key="asset.id">
                  <td><strong>{{ asset.name }}</strong><div class="code">{{ asset.jarvis_code }}</div></td>
                  <td>{{ asset.asset_type.name }}</td>
                  <td>{{ asset.location?.name || '–' }}</td>
                  <td>{{ asset.deleted_at ? new Date(asset.deleted_at).toLocaleString() : '–' }}</td>
                  <td class="text-right">
                    <v-btn
                      icon="mdi-eye-outline"
                      variant="text"
                      :to="{ path: `/assets/${asset.id}`, query: { archived: '1' } }"
                      aria-label="Archiviertes Asset ansehen"
                      title="Archiviertes Asset ansehen"
                    />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-window-item>

        <v-window-item value="distributions">
          <v-card-text v-if="distributions.length === 0" class="text-center py-10">
            Keine archivierten Verteilungen vorhanden.
          </v-card-text>
          <div v-else class="table-scroll">
            <v-table hover>
              <thead><tr><th>Bezeichnung</th><th>Typ</th><th>Standort</th><th>Archiviert</th><th /></tr></thead>
              <tbody>
                <tr v-for="distribution in distributions" :key="distribution.id">
                  <td><strong>{{ distribution.display_name }}</strong><div class="code">{{ distribution.asset.jarvis_code }}</div></td>
                  <td>{{ distribution.distribution_type === 'main' ? 'Hauptverteilung' : 'Unterverteilung' }}</td>
                  <td>{{ distribution.asset.location_path }}</td>
                  <td>{{ distribution.deleted_at ? new Date(distribution.deleted_at).toLocaleString() : '–' }}</td>
                  <td class="text-right">
                    <v-btn
                      icon="mdi-eye-outline"
                      variant="text"
                      :to="distributionLocation(distribution.id)"
                      aria-label="Archivierte Verteilung ansehen"
                      title="Archivierte Verteilung ansehen"
                    />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-window-item>

        <v-window-item value="devices">
          <v-alert type="info" variant="tonal" density="compact" class="ma-4 mb-0">
            Hier findest du auch archivierte Sicherungen. Die ursprüngliche Verteilung,
            der Bereich sowie bekannte Reihen- und Modulpositionen bleiben erhalten.
          </v-alert>
          <v-card-text v-if="devices.length === 0" class="text-center py-10">
            Keine archivierten Schutzgeräte vorhanden.
          </v-card-text>
          <div v-else class="table-scroll">
            <v-table hover>
              <thead><tr><th>Gerät</th><th>Typ</th><th>Ursprüngliche Verteilung</th><th>Position</th><th>Archiviert</th><th /></tr></thead>
              <tbody>
                <tr v-for="device in devices" :key="device.id">
                  <td><strong>{{ device.asset.name }}</strong><div class="code">{{ device.asset.jarvis_code }}</div></td>
                  <td>{{ protectiveDeviceLabels[device.device_type] }}</td>
                  <td>{{ device.distribution_name }}<div v-if="device.area_name" class="text-caption">{{ device.area_name }}</div></td>
                  <td>
                    <span v-if="device.row_number">Reihe {{ device.row_number }}</span>
                    <span v-else>Position unbekannt</span>
                    <span v-if="device.start_position"> · Modul {{ device.start_position }}</span>
                  </td>
                  <td>{{ device.deleted_at ? new Date(device.deleted_at).toLocaleString() : '–' }}</td>
                  <td class="text-right">
                    <v-btn
                      icon="mdi-electric-switch"
                      variant="text"
                      :to="distributionLocation(device.distribution_id)"
                      aria-label="Ursprüngliche Verteilung öffnen"
                      title="Ursprüngliche Verteilung öffnen"
                    />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-window-item>

        <v-window-item value="wiki">
          <v-card-text v-if="wikiPages.length === 0" class="text-center py-10">
            Keine archivierten Wiki-Seiten vorhanden.
          </v-card-text>
          <div v-else class="table-scroll">
            <v-table hover>
              <thead><tr><th>Titel</th><th>Pfad</th><th>Zuletzt geändert</th><th /></tr></thead>
              <tbody>
                <tr v-for="page in wikiPages" :key="page.id">
                  <td><strong>{{ page.title }}</strong></td>
                  <td>{{ page.path }}</td>
                  <td>{{ new Date(page.updated_at).toLocaleString() }}</td>
                  <td class="text-right">
                    <v-btn
                      icon="mdi-eye-outline"
                      variant="text"
                      :to="{ path: '/wiki', query: { page: page.id, archived: '1' } }"
                      aria-label="Archivierte Wiki-Seite ansehen"
                      title="Archivierte Wiki-Seite ansehen"
                    />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-window-item>

        <v-window-item value="consumption">
          <v-card-text v-if="consumptionMeters.length === 0" class="text-center py-10">
            Keine archivierten Verbrauchszähler vorhanden.
          </v-card-text>
          <div v-else class="table-scroll">
            <v-table hover>
              <thead><tr><th>Name</th><th>Typ</th><th>Letzter Stand</th><th>Zuordnung</th><th /></tr></thead>
              <tbody>
                <tr v-for="meter in consumptionMeters" :key="meter.id">
                  <td><strong>{{ meter.name }}</strong><div class="code">{{ meter.serial_number || meter.id }}</div></td>
                  <td>{{ consumptionMeterTypeLabels[meter.meter_type] }}</td>
                  <td>{{ meter.latest_value === null ? '–' : `${meter.latest_value.toLocaleString('de-DE')} ${meter.unit}` }}</td>
                  <td>{{ meter.asset_name || meter.location_path || '–' }}</td>
                  <td class="text-right">
                    <v-btn
                      icon="mdi-eye-outline"
                      variant="text"
                      :to="{ path: '/consumption', query: { tab: 'meters', meter: meter.id, archived: '1' } }"
                      aria-label="Archivierten Zähler ansehen"
                      title="Archivierten Zähler ansehen"
                    />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </div>
        </v-window-item>
      </v-window>
    </v-card>
  </v-container>
</template>

<style scoped>
.archive-container { max-width: 1440px; }
h1 { font-size: clamp(1.7rem, 4vw, 2.2rem); }
.table-scroll { overflow-x: auto; }
th { white-space: nowrap; }
.code { color: rgb(var(--v-theme-primary)); font-family: ui-monospace, SFMono-Regular, Consolas, monospace; font-size: .76rem; }
</style>
