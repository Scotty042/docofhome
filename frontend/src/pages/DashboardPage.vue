<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDisplay } from 'vuetify'

import { APP_NAME } from '../config/branding'
import { assetApi } from '../services/assetApi'
import { consumptionApi } from '../services/consumptionApi'
import { networkApi } from '../services/networkApi'
import { qualityApi } from '../services/qualityApi'
import { releaseApi } from '../services/releaseApi'
import { workItemsApi } from '../services/workItemsApi'
import { useSettingsStore } from '../stores/settings'
import type {
  ConsumptionComparison,
  ConsumptionReadingReminder
} from '../types/consumption'
import type { DashboardCardSetting } from '../types/release'
import type { WorkItemRead, WorkSummary } from '../types/work'

type CardId = DashboardCardSetting['id']

const { mdAndUp } = useDisplay()
const settings = useSettingsStore()
const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const assetCount = ref<number | null>(null)
const workSummary = ref<WorkSummary | null>(null)
const upcomingWork = ref<WorkItemRead[]>([])
const reminders = ref<ConsumptionReadingReminder[]>([])
const comparisons = ref<ConsumptionComparison[]>([])
const qualityScore = ref<number | null>(null)
const networkDevices = ref<number | null>(null)
const cards = ref<DashboardCardSetting[]>([])
const editMode = ref(false)
const draggedId = ref<CardId | null>(null)
const dragOverId = ref<CardId | null>(null)
const originalCards = ref<DashboardCardSetting[]>([])

const installationName = computed(() => settings.configuration?.installation_name ?? APP_NAME)
const visibleCards = computed(() => cards.value.filter((item) => item.visible))
const criticalItems = computed(() => {
  const rows = [
    ...upcomingWork.value
      .filter((item) => !item.automation_key?.startsWith('meter-reading:'))
      .map((item) => ({
        id: `work-${item.id}`,
        title: item.title,
        subtitle: item.due_at ? formatDate(item.due_at) : 'Ohne Termin',
        days: item.days_remaining,
        status: item.due_status,
        to: '/maintenance'
      })),
    ...reminders.value.map((item) => ({
      id: `meter-${item.meter_id}`,
      title: `${item.meter_name} ablesen`,
      subtitle: formatDate(item.due_at),
      days: item.days_remaining,
      status: item.status,
      to: `/consumption?read=${item.meter_id}`
    }))
  ]
  const unique = new Map<string, (typeof rows)[number]>()
  for (const row of rows) {
    const key = `${row.title.trim().toLocaleLowerCase()}|${row.subtitle}`
    if (!unique.has(key)) unique.set(key, row)
  }
  return [...unique.values()].sort((left, right) => (left.days ?? 9999) - (right.days ?? 9999))
})
const visibleCriticalItems = computed(() => criticalItems.value.slice(0, 8))

const defaultDashboardCards: DashboardCardSetting[] = [
  { id: 'documentation', visible: true },
  { id: 'consumption_comparison', visible: true },
  { id: 'maintenance', visible: true },
  { id: 'quality', visible: true },
  { id: 'network', visible: true }
]

const cardMeta: Record<CardId, { title: string; icon: string }> = {
  documentation: { title: 'Dokumentation', icon: 'mdi-database-outline' },
  consumption_comparison: { title: 'Monatsverbrauch', icon: 'mdi-chart-line' },
  maintenance: { title: 'Wartung & Aufgaben', icon: 'mdi-format-list-checks' },
  quality: { title: 'Dokumentationsqualität', icon: 'mdi-clipboard-check-outline' },
  network: { title: 'Netzwerk', icon: 'mdi-lan' }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium' }).format(new Date(value))
}

function formatValue(value: number | null, decimals: number, unit: string | null) {
  if (value === null) return 'Nicht verfügbar'
  const formatted = new Intl.NumberFormat('de-DE', {
    minimumFractionDigits: 0,
    maximumFractionDigits: decimals
  }).format(value)
  return `${formatted}${unit ? ` ${unit}` : ''}`
}

function trendIcon(trend: ConsumptionComparison['trend']) {
  if (trend === 'increased') return 'mdi-trending-up'
  if (trend === 'decreased') return 'mdi-trending-down'
  if (trend === 'equal') return 'mdi-trending-neutral'
  return 'mdi-help-circle-outline'
}

function trendColor(trend: ConsumptionComparison['trend']) {
  if (trend === 'increased') return 'warning'
  if (trend === 'decreased') return 'success'
  return 'info'
}

function dueLabel(days: number | null) {
  if (days === null) return 'Termin offen'
  if (days < 0) return `${Math.abs(days)} Tag${Math.abs(days) === 1 ? '' : 'e'} überfällig`
  if (days === 0) return 'Heute fällig'
  return `In ${days} Tag${days === 1 ? '' : 'en'} fällig`
}


function cloneCards(values: DashboardCardSetting[]) {
  return values.map((item) => ({ ...item }))
}

function startEditing() {
  originalCards.value = cloneCards(cards.value)
  editMode.value = true
}

function cancelEditing() {
  cards.value = cloneCards(originalCards.value)
  editMode.value = false
  draggedId.value = null
  dragOverId.value = null
}

function startCardDrag(event: DragEvent, id: CardId) {
  if (!editMode.value) return
  draggedId.value = id
  dragOverId.value = id
  event.dataTransfer?.setData('text/plain', id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function markDragOver(id: CardId) {
  if (editMode.value && draggedId.value) dragOverId.value = id
}

function finishCardDrag() {
  draggedId.value = null
  dragOverId.value = null
}

function moveCard(id: CardId, offset: number) {
  const index = cards.value.findIndex((item) => item.id === id)
  const target = index + offset
  if (index < 0 || target < 0 || target >= cards.value.length) return
  const copy = [...cards.value]
  const [item] = copy.splice(index, 1)
  if (item) copy.splice(target, 0, item)
  cards.value = copy
}

function dropCard(targetId: CardId) {
  if (!draggedId.value || draggedId.value === targetId) {
    finishCardDrag()
    return
  }
  const source = cards.value.findIndex((item) => item.id === draggedId.value)
  const target = cards.value.findIndex((item) => item.id === targetId)
  if (source < 0 || target < 0) {
    finishCardDrag()
    return
  }
  const copy = [...cards.value]
  const [item] = copy.splice(source, 1)
  if (item) copy.splice(target, 0, item)
  cards.value = copy
  finishCardDrag()
}

async function saveLayout() {
  saving.value = true
  try {
    const result = await releaseApi.saveDashboard({ cards: cards.value })
    cards.value = result.cards
    originalCards.value = cloneCards(result.cards)
    editMode.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dashboard konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

function resetLayout() {
  cards.value = cloneCards(defaultDashboardCards)
}

onMounted(async () => {
  try {
    if (!settings.configuration) await settings.fetchConfiguration()
    const [
      assetPage,
      dashboard,
      comparisonRows,
      dueWork,
      meterReminders,
      summary,
      quality,
      network
    ] = await Promise.all([
      assetApi.list({ page: 1, page_size: 1 }),
      releaseApi.dashboard(),
      consumptionApi.dashboardComparisons(),
      workItemsApi.upcoming(3),
      consumptionApi.readingReminders(3),
      workItemsApi.summary(),
      qualityApi.latest().catch(() => null),
      networkApi.summary().catch(() => null)
    ])
    assetCount.value = assetPage.total
    cards.value = dashboard.cards
    comparisons.value = comparisonRows
    upcomingWork.value = dueWork
    reminders.value = meterReminders
    workSummary.value = summary
    qualityScore.value = quality?.score ?? null
    networkDevices.value = network?.device_count ?? null
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dashboard konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <v-container class="pa-4 pa-md-6" fluid>
    <div class="d-flex flex-wrap align-center ga-3 mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">Willkommen bei {{ installationName }}</h1>
        <p class="text-medium-emphasis">Dein DocOfHome-Dashboard auf einen Blick.</p>
      </div>
      <v-spacer />
      <v-btn
        color="primary"
        size="large"
        prepend-icon="mdi-counter"
        to="/consumption?capture=1"
        class="meter-reading-button"
      >
        Zählerstände erfassen
      </v-btn>
      <v-btn
        v-if="mdAndUp"
        :prepend-icon="editMode ? 'mdi-close' : 'mdi-view-dashboard-edit-outline'"
        variant="tonal"
        @click="editMode ? cancelEditing() : startEditing()"
      >
        {{ editMode ? 'Änderungen verwerfen' : 'Dashboard bearbeiten' }}
      </v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-5">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-5" />

    <v-card
      v-if="criticalItems.length"
      title="Fälligkeiten und Erinnerungen"
      prepend-icon="mdi-alert-circle-outline"
      class="mb-5 compact-due-card"
      color="warning"
      variant="tonal"
    >
      <v-list bg-color="transparent" density="compact" lines="one">
        <v-list-item
          v-for="item in visibleCriticalItems"
          :key="item.id"
          :to="item.to"
          class="compact-due-item"
        >
          <v-list-item-title class="text-body-2">
            <strong>{{ item.title }}</strong>
            <span class="text-medium-emphasis"> · {{ item.subtitle }}</span>
          </v-list-item-title>
          <template #append>
            <v-chip size="small" :color="item.status === 'overdue' ? 'error' : item.status === 'today' ? 'warning' : 'info'">
              {{ dueLabel(item.days) }}
            </v-chip>
          </template>
        </v-list-item>
      </v-list>
      <v-card-actions v-if="criticalItems.length > visibleCriticalItems.length" class="pt-0">
        <v-spacer />
        <v-btn variant="text" size="small" to="/maintenance">Alle Fälligkeiten anzeigen</v-btn>
      </v-card-actions>
    </v-card>

    <v-card v-if="editMode && mdAndUp" class="mb-5" title="Dashboard konfigurieren">
      <v-card-text>
        <p class="text-medium-emphasis mb-3">
          Kacheln ziehen oder mit den Pfeilen sortieren. Diese Reihenfolge gilt anschließend auch mobil.
        </p>
        <div class="d-flex flex-wrap ga-2">
          <v-chip
            v-for="(card, index) in cards"
            :key="card.id"
            :prepend-icon="cardMeta[card.id].icon"
          >
            <v-checkbox-btn v-model="card.visible" :aria-label="`${cardMeta[card.id].title} anzeigen`" />
            {{ cardMeta[card.id].title }}
            <v-btn
              icon="mdi-arrow-left"
              size="x-small"
              variant="text"
              :disabled="index === 0"
              :aria-label="`${cardMeta[card.id].title} nach vorn`"
              @click="moveCard(card.id, -1)"
            />
            <v-btn
              icon="mdi-arrow-right"
              size="x-small"
              variant="text"
              :disabled="index === cards.length - 1"
              :aria-label="`${cardMeta[card.id].title} nach hinten`"
              @click="moveCard(card.id, 1)"
            />
          </v-chip>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn variant="text" prepend-icon="mdi-restore" @click="resetLayout">Standardlayout</v-btn>
        <v-spacer />
        <v-btn variant="text" @click="cancelEditing">Abbrechen</v-btn>
        <v-btn color="primary" prepend-icon="mdi-content-save" :loading="saving" @click="saveLayout">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>

    <v-row>
      <v-col
        v-for="card in visibleCards"
        :key="card.id"
        cols="12"
        :md="card.id === 'consumption_comparison' ? 8 : 4"
        class="dashboard-card-column"
        :class="{ 'dashboard-card-dragging': draggedId === card.id, 'dashboard-card-drop-target': dragOverId === card.id && draggedId !== card.id }"
        :draggable="editMode"
        @dragstart="startCardDrag($event, card.id)"
        @dragover.prevent="markDragOver(card.id)"
        @drop.prevent="dropCard(card.id)"
        @dragend="finishCardDrag"
      >
        <div v-if="editMode" class="dashboard-drag-toolbar" title="Kachel ziehen und an der gewünschten Position ablegen">
          <v-icon icon="mdi-drag-horizontal-variant" />
          <span>{{ cardMeta[card.id].title }}</span>
        </div>
        <v-card
          v-if="card.id === 'documentation'"
          title="Dokumentation"
          prepend-icon="mdi-database-outline"
          height="100%"
          :to="editMode ? undefined : '/assets'"
        >
          <v-card-text>
            <div class="metric">{{ assetCount ?? '…' }}</div>
            <div class="text-medium-emphasis">Assets erfasst</div>
          </v-card-text>
        </v-card>

        <v-card
          v-else-if="card.id === 'consumption_comparison'"
          title="Monatsverbrauch"
          prepend-icon="mdi-chart-line"
          height="100%"
          :to="editMode ? undefined : '/consumption'"
        >
          <v-card-text>
            <v-row dense>
              <v-col v-for="item in comparisons" :key="item.medium" cols="12" sm="6" lg="3">
                <div class="comparison">
                  <div class="font-weight-bold">{{ item.name }}</div>
                  <div class="text-h6">{{ formatValue(item.current_value, item.decimals, item.unit) }}</div>
                  <div class="text-caption text-medium-emphasis">
                    Vormonat: {{ formatValue(item.previous_value, item.decimals, item.unit) }}
                  </div>
                  <v-chip
                    size="small"
                    class="mt-2"
                    :color="trendColor(item.trend)"
                    :prepend-icon="trendIcon(item.trend)"
                  >
                    <template v-if="item.comparison_available">
                      {{ formatValue(item.difference, item.decimals, item.unit) }}
                      <span v-if="item.percent_change !== null">
                        ({{ item.percent_change.toFixed(1) }} %)
                      </span>
                    </template>
                    <template v-else>Keine Vergleichsbasis</template>
                  </v-chip>
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <v-card
          v-else-if="card.id === 'maintenance'"
          title="Wartung & Aufgaben"
          prepend-icon="mdi-format-list-checks"
          height="100%"
          :to="editMode ? undefined : '/maintenance'"
        >
          <v-card-text>
            <div class="metric">{{ workSummary?.open_total ?? '…' }}</div>
            <div>{{ workSummary?.due_next_3_days ?? '…' }} in den nächsten drei Tagen</div>
            <div class="text-error">{{ workSummary?.overdue ?? '…' }} überfällig</div>
          </v-card-text>
        </v-card>

        <v-card
          v-else-if="card.id === 'quality'"
          title="Dokumentationsqualität"
          prepend-icon="mdi-clipboard-check-outline"
          height="100%"
          :to="editMode ? undefined : '/quality'"
        >
          <v-card-text>
            <div class="metric">{{ qualityScore ?? '–' }}</div>
            <div class="text-medium-emphasis">Qualitätswert von 100</div>
          </v-card-text>
        </v-card>

        <v-card
          v-else-if="card.id === 'network'"
          title="Netzwerk"
          prepend-icon="mdi-lan"
          height="100%"
          :to="editMode ? undefined : '/network'"
        >
          <v-card-text>
            <div class="metric">{{ networkDevices ?? '–' }}</div>
            <div class="text-medium-emphasis">Dokumentierte Netzwerkgeräte</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.metric {
  font-size: 2.25rem;
  font-weight: 700;
}

.dashboard-card-column {
  transition: opacity 120ms ease, outline-color 120ms ease, transform 120ms ease;
}

.dashboard-card-column[draggable="true"] {
  cursor: grab;
}

.dashboard-card-column[draggable="true"]:active {
  cursor: grabbing;
}

.dashboard-card-dragging {
  opacity: 0.45;
}

.dashboard-card-drop-target {
  outline: 3px dashed rgb(var(--v-theme-primary));
  outline-offset: -6px;
  border-radius: 16px;
}

.dashboard-drag-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.35rem;
  padding: 0.35rem 0.65rem;
  color: rgb(var(--v-theme-primary));
  font-size: 0.8rem;
  font-weight: 700;
  user-select: none;
}

.comparison {
  min-height: 128px;
  padding: 0.75rem;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
}

.compact-due-card :deep(.v-card-title) {
  min-height: 44px;
  padding-top: 10px;
  padding-bottom: 6px;
}

.compact-due-item {
  min-height: 38px;
}

@media (max-width: 600px) {
  .meter-reading-button {
    width: 100%;
    order: 3;
  }
}
</style>
