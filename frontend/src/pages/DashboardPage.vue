<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDisplay } from 'vuetify'

import { groupReadingReminders } from '../services/dashboardPresentation'
import { moduleKeys, type ModuleKey } from '../types/settings'
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

const activeModules = computed(() => new Set(settings.configuration?.enabled_modules ?? moduleKeys))
const moduleForCard: Record<CardId, ModuleKey> = { documentation: 'assets', consumption_comparison: 'consumption', maintenance: 'maintenance', quality: 'quality', network: 'network' }
const presentationComparisons = computed(() => {
  const order = ['gas', 'electricity', 'water', 'pv_generation', 'pv_feed_in']
  return [...comparisons.value].sort((a, b) => order.indexOf(a.medium) - order.indexOf(b.medium))
})
const readingGroups = computed(() => groupReadingReminders(reminders.value))
const dueTasks = computed(() => upcomingWork.value.filter(item => !item.automation_key?.startsWith('meter-reading:')))
const todayLabel = new Intl.DateTimeFormat('de-DE', { dateStyle: 'full', timeZone: settings.configuration?.timezone || 'Europe/Berlin' }).format(new Date())
const monthLabel = new Intl.DateTimeFormat('de-DE', { month: 'long', year: 'numeric', timeZone: settings.configuration?.timezone || 'Europe/Berlin' }).format(new Date())
const visibleCards = computed(() => cards.value.filter((item) => item.visible && activeModules.value.has(moduleForCard[item.id])))
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
  if (value === null) return 'Noch kein Monatswert'
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
  const failures: string[] = []
  cards.value = cloneCards(defaultDashboardCards)
  try {
    if (!settings.configuration) await settings.fetchConfiguration()
    const jobs: Array<{ module?: ModuleKey; label: string; run: () => Promise<void> }> = [
      { label: 'Dashboard-Einstellungen', run: async () => { cards.value = (await releaseApi.dashboard()).cards } },
      { module: 'assets', label: 'Inventar', run: async () => { assetCount.value = (await assetApi.list({ page: 1, page_size: 1 })).total } },
      { module: 'consumption', label: 'Monatsverbrauch', run: async () => { comparisons.value = await consumptionApi.dashboardComparisons() } },
      { module: 'consumption', label: 'Ableseerinnerungen', run: async () => { reminders.value = await consumptionApi.readingReminders(3) } },
      // Both work endpoints synchronize monthly tasks. Read them sequentially to avoid
      // concurrent creation of the same automatic task on a freshly due month.
      { module: 'maintenance', label: 'Aufgabenübersicht', run: async () => { upcomingWork.value = await workItemsApi.upcoming(3); workSummary.value = await workItemsApi.summary() } },
      { module: 'quality', label: 'Dokumentationsqualität', run: async () => { qualityScore.value = (await qualityApi.latest())?.score ?? null } },
      { module: 'network', label: 'Netzwerk', run: async () => { networkDevices.value = (await networkApi.summary()).device_count } }
    ]
    await Promise.all(jobs.filter(job => !job.module || activeModules.value.has(job.module)).map(async job => {
      try { await job.run() } catch { failures.push(job.label) }
    }))
    if (failures.length) error.value = `Nicht alle Bereiche konnten geladen werden: ${failures.join(', ')}. Die übrigen Angaben bleiben verfügbar.`
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Dashboard konnte nicht geladen werden.'
  } finally { loading.value = false }
})
</script>

<template>
  <v-container class="home-dashboard" fluid>
    <div class="home-page-header dashboard-heading">
      <div><div class="home-eyebrow">DEIN ZUHAUSE</div><h1>Alles im Blick.</h1><p>{{ todayLabel }}</p></div>
      <div class="home-inline-actions dashboard-heading-actions">
        <v-btn v-if="activeModules.has('consumption')" color="primary" size="large" prepend-icon="mdi-counter" to="/consumption?capture=1" class="meter-reading-button">Zählerstände erfassen<v-icon icon="mdi-chevron-right" end /></v-btn>
        <v-btn :icon="editMode ? 'mdi-close' : 'mdi-view-dashboard-edit-outline'" variant="text" :aria-label="editMode ? 'Dashboard-Anpassung schließen' : 'Dashboard anpassen'" :title="editMode ? 'Anpassung schließen' : 'Dashboard anpassen'" @click="editMode ? cancelEditing() : startEditing()" />
      </div>
    </div>
    <div v-if="activeModules.has('assets') || activeModules.has('maintenance')" class="dashboard-summary">
      <router-link v-if="activeModules.has('assets')" to="/assets"><v-icon icon="mdi-archive-outline" size="28" /><span><strong>{{ assetCount ?? '–' }} Geräte</strong><small>In deinem Zuhause</small></span></router-link>
      <router-link v-if="activeModules.has('maintenance')" to="/maintenance"><v-icon icon="mdi-checkbox-marked-outline" size="28" /><span><strong>{{ workSummary?.open_total ?? '–' }} offene Aufgaben</strong><small :class="workSummary?.overdue ? 'text-error' : 'text-success'">{{ workSummary ? `${workSummary.overdue} überfällig` : 'Wird geladen' }}</small></span></router-link>
    </div>
    <v-alert v-if="error" type="warning" variant="tonal" class="mb-5">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" indeterminate color="primary" class="mb-5" aria-label="Dashboard wird geladen" />
    <v-card v-if="editMode" class="mb-5" title="Dashboard anpassen">
      <v-card-text><p class="mb-4 home-context-help">Bereiche einblenden und ihre Reihenfolge ändern. Ziehen oder die Pfeiltasten verwenden.</p><div class="home-inline-actions"><div v-for="(card, index) in cards" :key="card.id" class="dashboard-config-item"><v-checkbox-btn v-model="card.visible" :aria-label="`${cardMeta[card.id].title} anzeigen`" /><span>{{ cardMeta[card.id].title }}</span><v-btn icon="mdi-arrow-left" variant="text" size="small" :disabled="index === 0" :aria-label="`${cardMeta[card.id].title} nach vorn`" @click="moveCard(card.id, -1)"/><v-btn icon="mdi-arrow-right" variant="text" size="small" :disabled="index === cards.length - 1" :aria-label="`${cardMeta[card.id].title} nach hinten`" @click="moveCard(card.id, 1)"/></div></div></v-card-text>
      <v-card-actions><v-btn variant="text" @click="resetLayout">Standardlayout</v-btn><v-spacer/><v-btn @click="cancelEditing">Abbrechen</v-btn><v-btn color="primary" :loading="saving" @click="saveLayout">Speichern</v-btn></v-card-actions>
    </v-card>
    <!-- Critical deadlines remain visible independently of optional dashboard cards. -->
    <v-card v-if="dueTasks.some(item => item.due_status === 'overdue')" class="mb-5" title="Überfällige Aufgaben" prepend-icon="mdi-alert-circle-outline">
      <v-list bg-color="transparent"><v-list-item v-for="item in dueTasks.filter(item => item.due_status === 'overdue')" :key="item.id" :title="item.title" :subtitle="item.due_at ? formatDate(item.due_at) : 'Termin prüfen'" to="/maintenance"><template #append><v-chip size="small" color="error">{{ dueLabel(item.days_remaining) }}</v-chip></template></v-list-item></v-list>
    </v-card>
    <div class="dashboard-grid">
      <section v-for="card in visibleCards" :key="card.id" :class="['dashboard-section', `dashboard-${card.id}`, { 'dashboard-card-dragging': draggedId === card.id, 'dashboard-card-drop-target': dragOverId === card.id && draggedId !== card.id }]" :draggable="editMode" @dragstart="startCardDrag($event, card.id)" @dragover.prevent="markDragOver(card.id)" @drop.prevent="dropCard(card.id)" @dragend="finishCardDrag">
        <v-card v-if="card.id === 'consumption_comparison'" class="consumption-overview" height="100%">
          <v-card-text><div class="dashboard-panel-heading"><h2><v-icon icon="mdi-chart-bar" size="25"/>Monatsverbrauch</h2><span><v-icon icon="mdi-calendar-month-outline" size="20"/>{{ monthLabel }}</span></div><p class="home-section-subtitle mt-2">Aktuelle Monatswerte und Vergleich zum Vormonat</p>
            <div v-if="!comparisons.length && !loading" class="home-empty"><v-icon icon="mdi-counter" size="38"/><h2>Noch keine Monatswerte</h2><p>Lege einen Zähler an oder prüfe deine Ablesungen.</p><v-btn to="/consumption" variant="text" color="primary" class="mt-3">Verbrauch öffnen</v-btn></div>
            <router-link v-for="item in presentationComparisons" :key="item.medium" class="consumption-overview-row" :to="item.meter_id ? `/consumption?read=${item.meter_id}` : '/consumption'">
              <span :class="['consumption-medium-icon', `medium-${item.medium}`]"><v-icon :icon="item.medium === 'gas' ? 'mdi-fire' : item.medium === 'water' ? 'mdi-water-outline' : item.medium.startsWith('pv') ? 'mdi-white-balance-sunny' : 'mdi-lightning-bolt-outline'" size="30"/></span>
              <div class="consumption-medium-data"><strong>{{ item.name }}<v-tooltip v-if="item.incomplete" text="Unvollständige Datenbasis"><template #activator="{ props }"><v-icon v-bind="props" icon="mdi-information-outline" size="16" class="ml-2" aria-label="Unvollständige Datenbasis" tabindex="0"/></template></v-tooltip></strong><div class="consumption-values"><div><small>Aktueller Monat</small><span :class="{ 'consumption-value': item.current_value !== null }">{{ formatValue(item.current_value, item.decimals, item.unit) }}</span></div><div><small>Vormonat</small><span>{{ item.previous_value === null ? '–' : formatValue(item.previous_value, item.decimals, item.unit) }}</span></div></div></div>
              <div class="consumption-trend" :class="item.comparison_available ? `text-${trendColor(item.trend)}` : ''"><template v-if="item.comparison_available"><strong><v-icon :icon="trendIcon(item.trend)" size="20"/>{{ item.percent_change === null ? '–' : `${new Intl.NumberFormat('de-DE', { maximumFractionDigits: 1 }).format(item.percent_change)} %` }}</strong><small>{{ formatValue(item.difference, item.decimals, item.unit) }}</small></template><template v-else><strong>–</strong><small>Kein Vergleich möglich</small></template></div>
            </router-link>
          </v-card-text>
        </v-card>
        <v-card v-else-if="card.id === 'maintenance'" class="deadline-overview" height="100%">
          <v-card-text><h2><v-icon icon="mdi-checkbox-marked-outline" size="25"/>Fälligkeiten und Aufgaben</h2><router-link class="deadline-work-summary" to="/maintenance"><v-icon icon="mdi-wrench-outline" size="26"/><span><strong>{{ workSummary?.open_total ?? '–' }} offene Aufgaben</strong><small :class="workSummary?.overdue ? 'text-error' : 'text-success'">{{ workSummary?.overdue ?? '–' }} überfällig</small></span><v-icon icon="mdi-chevron-right" size="20"/></router-link>
            <details v-for="group in readingGroups" :key="group.key" class="deadline-group" open><summary><span><strong>{{ group.items.length }} Zählerablesung{{ group.items.length === 1 ? '' : 'en' }}</strong><small>{{ formatDate(group.dueAt) }}</small></span><v-chip size="small" :color="group.status === 'overdue' ? 'error' : group.status === 'today' ? 'warning' : 'secondary'">{{ dueLabel(group.days) }}</v-chip></summary><router-link v-for="item in group.items" :key="item.meter_id" :to="`/consumption?read=${item.meter_id}`" class="deadline-reading"><v-icon icon="mdi-counter" size="19"/><span>{{ item.meter_name }} ablesen<small>{{ formatDate(item.due_at) }}</small></span><v-icon icon="mdi-chevron-right" size="17"/></router-link></details>
            <router-link v-for="item in dueTasks.filter(item => item.due_status !== 'overdue')" :key="item.id" to="/maintenance" class="deadline-reading"><v-icon icon="mdi-calendar-check-outline" size="20"/><span>{{ item.title }}<small>{{ dueLabel(item.days_remaining) }}</small></span><v-icon icon="mdi-chevron-right" size="17"/></router-link>
            <p v-if="!loading && !readingGroups.length && !dueTasks.length" class="home-context-help py-5">Keine Fälligkeiten in den nächsten drei Tagen.</p><v-btn to="/maintenance" variant="text" color="primary" append-icon="mdi-arrow-right" class="deadline-all">Alle Fälligkeiten anzeigen</v-btn>
          </v-card-text>
        </v-card>
        <v-card v-else :to="editMode ? undefined : card.id === 'documentation' ? '/assets' : card.id === 'quality' ? '/quality' : '/network'" class="dashboard-metric-card" height="100%"><v-card-text><h2><v-icon :icon="cardMeta[card.id].icon" size="24"/>{{ cardMeta[card.id].title }}</h2><strong class="dashboard-metric">{{ card.id === 'documentation' ? assetCount ?? '–' : card.id === 'quality' ? qualityScore ?? '–' : networkDevices ?? '–' }}</strong><p class="home-section-subtitle">{{ card.id === 'documentation' ? 'Geräte und Installationen' : card.id === 'quality' ? 'Qualitätswert von 100' : 'Dokumentierte Netzwerkgeräte' }}</p></v-card-text></v-card>
      </section>
      <v-card v-if="!visibleCards.some(card => card.id === 'maintenance') && readingGroups.length" class="dashboard-section dashboard-reminders" title="Anstehende Zählerablesungen" prepend-icon="mdi-counter"><v-list bg-color="transparent"><v-list-item v-for="item in reminders" :key="item.meter_id" :title="`${item.meter_name} ablesen`" :subtitle="`${formatDate(item.due_at)} · ${dueLabel(item.days_remaining)}`" :to="`/consumption?read=${item.meter_id}`"/></v-list></v-card>
    </div>
    <div v-if="!loading && !visibleCards.length" class="home-empty"><h2>Deine Übersicht, nach deinen Wünschen.</h2><p>Blende die gewünschten Bereiche über „Dashboard anpassen“ ein.</p><v-btn color="primary" class="mt-4" @click="startEditing">Dashboard anpassen</v-btn></div>
  </v-container>
</template>

<style scoped>
.home-dashboard{max-width:1540px}.dashboard-heading h1{font-size:clamp(2.5rem,4vw,3.5rem)!important}.dashboard-heading p{font-family:var(--home-serif);font-size:19px}.meter-reading-button{font-family:var(--home-serif);font-size:18px!important;height:58px!important}.dashboard-summary{display:flex;gap:0;border-bottom:1px solid var(--home-rule);padding:6px 0 25px;margin-bottom:26px}.dashboard-summary a{display:flex;align-items:center;gap:20px;text-decoration:none;color:inherit;padding:0 35px 0 10px}.dashboard-summary a+a{border-left:1px solid var(--home-rule);padding-left:35px}.dashboard-summary strong{font-size:19px;display:block}.dashboard-summary small{display:block;color:var(--home-muted);font-size:14px;margin-top:2px}.dashboard-grid{display:grid;grid-template-columns:repeat(12,minmax(0,1fr));gap:16px}.dashboard-section{grid-column:span 4;min-width:0}.dashboard-consumption_comparison{grid-column:span 7}.dashboard-maintenance,.dashboard-reminders{grid-column:span 5}.dashboard-panel-heading{display:flex;justify-content:space-between;align-items:center;gap:16px}.dashboard-panel-heading>span{font-size:14px;display:flex;gap:8px;align-items:center;color:var(--home-muted)}.dashboard-grid h2{font-family:var(--home-serif);font-size:25px;letter-spacing:-.5px;display:flex;align-items:center;gap:12px;line-height:1.35}.consumption-overview,.deadline-overview{min-height:540px}.consumption-overview>.v-card-text,.deadline-overview>.v-card-text{padding:24px}.consumption-overview-row{display:flex;align-items:flex-start;gap:22px;padding:30px 0;color:inherit;text-decoration:none}.consumption-overview-row:hover{background:var(--home-soft)}.consumption-overview-row+.consumption-overview-row{border-top:1px solid var(--home-rule)}.consumption-medium-icon{height:56px;width:56px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--home-sage);flex-shrink:0}.medium-gas{background:rgba(var(--v-theme-warning),.12);color:rgb(var(--v-theme-warning))}.medium-water{background:rgba(var(--v-theme-info),.12);color:rgb(var(--v-theme-info))}.consumption-medium-data{flex:1;min-width:0}.consumption-medium-data>strong{font-size:18px;font-weight:600}.consumption-values{display:flex;gap:20px;margin-top:12px;align-items:center}.consumption-values>div{min-width:0;flex:1}.consumption-values>div+div{padding-left:20px;border-left:1px solid var(--home-rule)}.consumption-values small{color:var(--home-muted);font-size:13px;display:block;margin-bottom:4px}.consumption-values span{display:block;font-size:16px}.consumption-values .consumption-value{font-family:var(--home-serif);font-size:25px;font-weight:700}.consumption-trend{align-self:center;text-align:center;min-width:108px;padding:10px 6px;border-radius:7px;background:var(--home-soft);margin-top:20px}.consumption-trend strong{display:flex;align-items:center;justify-content:center;gap:5px;font-size:20px}.consumption-trend small{display:block;font-size:12px;color:var(--home-muted)}.deadline-work-summary{display:flex;align-items:center;gap:14px;padding:21px 0;color:inherit;text-decoration:none;border-bottom:1px solid var(--home-rule)}.deadline-work-summary span{flex:1}.deadline-work-summary strong{display:block;font-size:17px}.deadline-work-summary small{display:block;font-size:14px;margin-top:3px}.deadline-group summary{display:flex;align-items:center;gap:12px;padding:17px 0;cursor:pointer;list-style:none}.deadline-group summary::before{content:'';display:none}.deadline-group summary::marker{display:none}.deadline-group summary>span:first-child{flex:1;min-width:0}.deadline-group summary>.v-chip{flex:0 0 auto}.deadline-group strong{display:block;font-size:16px;font-weight:600}.deadline-group small{display:block;font-size:12px;color:var(--home-muted);margin-top:3px}.deadline-group summary::-webkit-details-marker{display:none}.deadline-group{border-bottom:1px solid var(--home-rule)}.deadline-reading{display:flex;gap:10px;align-items:center;padding:11px 0;color:inherit;text-decoration:none;font-size:14px;line-height:1.3}.deadline-reading>span{flex:1;overflow-wrap:anywhere}.deadline-reading small{display:inline;font-size:12px;color:var(--home-muted);margin-left:6px}.deadline-reading:hover{background:var(--home-soft)}.deadline-all{margin-top:15px;padding-inline:0!important;font-size:14px;max-width:100%}.dashboard-metric{font-family:var(--home-serif);font-size:36px;display:block;margin-top:22px}.dashboard-metric-card .v-card-text{padding:24px}.dashboard-config-item{display:flex;align-items:center;gap:4px;font-size:14px;border:1px solid var(--home-rule);padding:5px 8px;border-radius:7px}.dashboard-card-dragging{opacity:.5}.dashboard-card-drop-target{outline:3px dashed rgb(var(--v-theme-primary));outline-offset:3px}.dashboard-section[draggable=true]{cursor:grab}
@media(max-width:1279px){.dashboard-consumption_comparison{grid-column:span 12}.dashboard-maintenance,.dashboard-reminders{grid-column:span 12}.consumption-overview,.deadline-overview{min-height:0}.deadline-group .deadline-reading{padding-block:11px}.dashboard-section:not(.dashboard-consumption_comparison):not(.dashboard-maintenance):not(.dashboard-reminders){grid-column:span 6}.dashboard-heading-actions{gap:5px}}
@media(max-width:599px){.dashboard-heading h1{font-size:2.65rem!important}.dashboard-heading p{font-size:16px}.dashboard-heading-actions{width:100%}.dashboard-heading-actions>.meter-reading-button{flex:1;font-size:15px!important;height:48px!important}.dashboard-heading-actions>.v-btn--icon{width:38px}.dashboard-summary{padding:3px 0 22px;margin-bottom:22px}.dashboard-summary a{padding:0 10px 0 0;gap:10px;flex:1;min-width:0}.dashboard-summary a+a{padding-left:15px}.dashboard-summary strong{font-size:15px}.dashboard-summary small{font-size:12px}.dashboard-grid{gap:18px}.dashboard-section{grid-column:span 12!important}.dashboard-grid h2{font-size:23px;gap:9px}.dashboard-panel-heading{flex-wrap:wrap;gap:8px}.dashboard-panel-heading>span{font-size:13px}.consumption-overview-row{display:grid;grid-template-columns:43px minmax(0,1fr);gap:13px;padding:24px 0}.consumption-medium-icon{height:43px;width:43px}.consumption-medium-icon .v-icon{font-size:25px!important}.consumption-values{gap:14px}.consumption-values>div+div{padding-left:14px}.consumption-values span{font-size:14px}.consumption-values .consumption-value{font-size:23px}.consumption-values small{font-size:11px}.consumption-trend{grid-column:2;justify-self:start;display:flex;gap:12px;align-items:center;min-width:0;margin:0;padding:5px 10px}.consumption-trend strong{font-size:17px}.consumption-trend small{font-size:11px}.deadline-group summary{gap:8px}.deadline-group .v-chip{font-size:11px}.deadline-all{font-size:13px}}
</style>
