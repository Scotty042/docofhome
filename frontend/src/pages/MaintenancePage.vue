<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { consumptionApi } from '../services/consumptionApi'
import { workItemsApi } from '../services/workItemsApi'
import type { ConsumptionReadingReminder } from '../types/consumption'
import type {
  WorkItemRead,
  RecurrenceMode,
  WorkItemType,
  WorkItemWrite,
  WorkPriority,
  WorkStatus,
  WorkSummary
} from '../types/work'

const items = ref<WorkItemRead[]>([])
const readingReminders = ref<ConsumptionReadingReminder[]>([])
const summary = ref<WorkSummary | null>(null)
const loading = ref(false)
const saving = ref(false)
const actionId = ref<string | null>(null)
const error = ref<string | null>(null)
const statusFilter = ref<WorkStatus | 'all'>('open')
const typeFilter = ref<WorkItemType | 'all'>('all')
const dialog = ref(false)
const editing = ref<WorkItemRead | null>(null)
const form = ref({
  item_type: 'task' as WorkItemType,
  title: '',
  description: '',
  due_at: '',
  recurrence_days: null as number | null,
  recurrence_mode: 'none' as RecurrenceMode,
  calendar_months: 1 as number | null,
  calendar_day: null as number | null,
  calendar_month: null as number | null,
  calendar_last_day: false,
  priority: 'normal' as WorkPriority
})

const filteredItems = computed(() => items.value.filter((item) => (
  (statusFilter.value === 'all' || item.status === statusFilter.value)
  && (typeFilter.value === 'all' || item.item_type === typeFilter.value)
)))

function toLocalInput(value: string | null): string {
  if (!value) return ''
  const date = new Date(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

function toIso(value: string): string | null {
  return value ? new Date(value).toISOString() : null
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const [loadedItems, loadedSummary, loadedReadingReminders] = await Promise.all([
      workItemsApi.list(),
      workItemsApi.summary(),
      consumptionApi.readingReminders(31)
    ])
    items.value = loadedItems
    summary.value = loadedSummary
    readingReminders.value = loadedReadingReminders
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Wartungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editing.value = null
  form.value = {
    item_type: 'task',
    title: '',
    description: '',
    due_at: '',
    recurrence_days: null,
    recurrence_mode: 'none',
    calendar_months: 1,
    calendar_day: null,
    calendar_month: null,
    calendar_last_day: false,
    priority: 'normal'
  }
  dialog.value = true
}

function startEdit(item: WorkItemRead) {
  editing.value = item
  form.value = {
    item_type: item.item_type,
    title: item.title,
    description: item.description ?? '',
    due_at: toLocalInput(item.due_at),
    recurrence_days: item.recurrence_days,
    recurrence_mode: item.recurrence_mode,
    calendar_months: item.calendar_months,
    calendar_day: item.calendar_day,
    calendar_month: item.calendar_month,
    calendar_last_day: item.calendar_last_day,
    priority: item.priority
  }
  dialog.value = true
}

async function save() {
  if (!form.value.title.trim()) return
  saving.value = true
  error.value = null
  const payload: WorkItemWrite = {
    item_type: form.value.item_type,
    title: form.value.title.trim(),
    description: form.value.description.trim() || null,
    target_type: editing.value?.target_type ?? null,
    target_id: editing.value?.target_id ?? null,
    due_at: toIso(form.value.due_at),
    recurrence_days: form.value.item_type === 'maintenance' && form.value.recurrence_mode === 'interval' ? form.value.recurrence_days : null,
    recurrence_mode: form.value.item_type === 'maintenance' ? form.value.recurrence_mode : 'none',
    calendar_months: form.value.item_type === 'maintenance' && form.value.recurrence_mode === 'calendar' ? form.value.calendar_months : null,
    calendar_day: form.value.item_type === 'maintenance' && form.value.recurrence_mode === 'calendar' && !form.value.calendar_last_day ? form.value.calendar_day : null,
    calendar_month: form.value.item_type === 'maintenance' && form.value.recurrence_mode === 'calendar' ? form.value.calendar_month : null,
    calendar_last_day: form.value.item_type === 'maintenance' && form.value.recurrence_mode === 'calendar' ? form.value.calendar_last_day : false,
    priority: form.value.priority
  }
  try {
    if (editing.value) await workItemsApi.update(editing.value.id, payload)
    else await workItemsApi.create(payload)
    dialog.value = false
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Eintrag konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function act(item: WorkItemRead, action: 'complete' | 'cancel' | 'reopen' | 'delete') {
  actionId.value = item.id
  error.value = null
  try {
    if (action === 'complete') await workItemsApi.complete(item.id)
    if (action === 'cancel') await workItemsApi.cancel(item.id)
    if (action === 'reopen') await workItemsApi.reopen(item.id)
    if (action === 'delete') await workItemsApi.remove(item.id)
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Aktion konnte nicht ausgeführt werden.'
  } finally {
    actionId.value = null
  }
}

function statusLabel(status: WorkStatus): string {
  return { open: 'Offen', completed: 'Erledigt', cancelled: 'Abgebrochen' }[status]
}

function typeLabel(type: WorkItemType): string {
  return type === 'maintenance' ? 'Wartung' : 'Aufgabe'
}

onMounted(() => void load())
</script>

<template>
  <v-container class="maintenance-page pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-5">
      <div>
        <h1>Wartung & Aufgaben</h1>
        <p class="text-medium-emphasis mb-0">Fälligkeiten, Wiederholungen und erledigte Arbeiten im Blick behalten.</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="startCreate">Neuer Eintrag</v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <v-row class="mb-2">
      <v-col cols="6" md="3"><v-card title="Offen"><v-card-text class="metric">{{ summary?.open_total ?? '…' }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Überfällig"><v-card-text class="metric text-error">{{ summary?.overdue ?? '…' }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Nächste 7 Tage"><v-card-text class="metric">{{ summary?.due_next_7_days ?? '…' }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Erledigt"><v-card-text class="metric">{{ summary?.completed_total ?? '…' }}</v-card-text></v-card></v-col>
    </v-row>


    <v-card class="mb-4" title="Ableseerinnerungen" prepend-icon="mdi-counter">
      <v-list v-if="readingReminders.length" lines="two">
        <v-list-item v-for="reminder in readingReminders" :key="reminder.meter_id">
          <template #prepend><v-icon icon="mdi-counter" /></template>
          <v-list-item-title>{{ reminder.meter_name }}</v-list-item-title>
          <v-list-item-subtitle>
            {{ new Date(reminder.due_at).toLocaleDateString() }} ·
            <span v-if="reminder.days_remaining > 0">in {{ reminder.days_remaining }} Tagen</span>
            <span v-else-if="reminder.days_remaining === 0">heute fällig</span>
            <span v-else class="text-error">{{ Math.abs(reminder.days_remaining) }} Tage überfällig</span>
          </v-list-item-subtitle>
          <template #append>
            <v-btn color="primary" variant="tonal" prepend-icon="mdi-plus" :to="{ path: '/consumption', query: { read: reminder.meter_id } }">Jetzt ablesen</v-btn>
          </template>
        </v-list-item>
      </v-list>
      <v-card-text v-else-if="!loading && !error" class="text-medium-emphasis">
        Aktuell ist keine Zählerablesung fällig. Berücksichtigt werden monatliche
        Ablesepläne und die globale Fälligkeit nach der letzten Ablesung.
      </v-card-text>
    </v-card>

    <v-card>
      <v-card-text class="d-flex flex-wrap ga-3">
        <v-select
          v-model="statusFilter"
          :items="[
            { title: 'Alle Status', value: 'all' },
            { title: 'Offen', value: 'open' },
            { title: 'Erledigt', value: 'completed' },
            { title: 'Abgebrochen', value: 'cancelled' }
          ]"
          label="Status"
          density="compact"
          hide-details
          max-width="220"
        />
        <v-select
          v-model="typeFilter"
          :items="[
            { title: 'Alle Typen', value: 'all' },
            { title: 'Aufgaben', value: 'task' },
            { title: 'Wartungen', value: 'maintenance' }
          ]"
          label="Typ"
          density="compact"
          hide-details
          max-width="220"
        />
      </v-card-text>
      <v-list v-if="filteredItems.length" lines="three">
        <v-list-item
          v-for="item in filteredItems"
          :key="item.id"
          :prepend-icon="item.item_type === 'maintenance' ? 'mdi-format-list-checks' : 'mdi-check-circle-outline'"
        >
          <v-list-item-title class="d-flex flex-wrap align-center ga-2">
            <span>{{ item.title }}</span>
            <v-chip size="x-small" variant="tonal">{{ typeLabel(item.item_type) }}</v-chip>
            <v-chip v-if="item.generated" size="x-small" color="info" variant="tonal">Automatisch</v-chip>
            <v-chip size="x-small" :color="item.overdue ? 'error' : undefined" variant="tonal">{{ statusLabel(item.status) }}</v-chip>
          </v-list-item-title>
          <v-list-item-subtitle>
            <div v-if="item.target_label">
              <router-link v-if="item.target_route" :to="item.target_route">{{ item.target_label }}</router-link>
              <span v-else>{{ item.target_label }}</span>
            </div>
            <div :class="item.overdue ? 'text-error font-weight-bold' : ''">
              {{ item.due_at ? new Date(item.due_at).toLocaleString() : 'Keine Fälligkeit' }}
              <span v-if="item.recurrence_days"> · alle {{ item.recurrence_days }} Tage</span>
            </div>
            <div v-if="item.description" class="text-truncate">{{ item.description }}</div>
          </v-list-item-subtitle>
          <template #append>
            <div class="d-flex flex-wrap ga-1">
              <v-btn v-if="item.generated && item.target_route && item.status === 'open'" icon="mdi-counter" size="small" color="primary" variant="tonal" aria-label="Zähler ablesen" :to="item.target_route" />
              <v-btn v-if="item.status === 'open' && !item.generated" icon="mdi-pencil" size="small" variant="text" aria-label="Bearbeiten" @click="startEdit(item)" />
              <v-btn v-if="item.status === 'open' && !item.generated" icon="mdi-check" size="small" color="success" variant="tonal" :loading="actionId === item.id" aria-label="Erledigen" @click="act(item, 'complete')" />
              <v-btn v-if="item.status === 'open' && !item.generated" icon="mdi-close" size="small" variant="text" aria-label="Abbrechen" @click="act(item, 'cancel')" />
              <v-btn v-else-if="!item.generated" icon="mdi-refresh" size="small" variant="text" aria-label="Wieder öffnen" @click="act(item, 'reopen')" />
              <v-btn v-if="!item.generated" icon="mdi-delete-outline" size="small" color="error" variant="text" aria-label="Löschen" @click="act(item, 'delete')" />
            </div>
          </template>
        </v-list-item>
      </v-list>
      <v-card-text v-else class="text-medium-emphasis">Keine passenden Einträge vorhanden.</v-card-text>
    </v-card>

    <v-dialog v-model="dialog" max-width="700">
      <v-card :title="editing ? 'Eintrag bearbeiten' : 'Eintrag anlegen'" prepend-icon="mdi-format-list-checks">
        <v-card-text>
          <v-select
            v-model="form.item_type"
            :items="[
              { title: 'Aufgabe', value: 'task' },
              { title: 'Wartung', value: 'maintenance' }
            ]"
            label="Typ"
          />
          <v-text-field v-model="form.title" label="Titel" maxlength="200" counter autofocus />
          <v-textarea v-model="form.description" label="Beschreibung" rows="5" />
          <v-text-field v-model="form.due_at" label="Fällig am" type="datetime-local" />
          <v-select
            v-if="form.item_type === 'maintenance'"
            v-model="form.recurrence_mode"
            :items="[
              { title: 'Keine Wiederholung', value: 'none' },
              { title: 'Festes Tagesintervall', value: 'interval' },
              { title: 'Kalenderregel', value: 'calendar' }
            ]"
            label="Wiederholung"
          />
          <v-text-field
            v-if="form.item_type === 'maintenance' && form.recurrence_mode === 'interval'"
            v-model.number="form.recurrence_days"
            label="Wiederholung in Tagen"
            type="number"
            min="1"
            max="3650"
            clearable
          />
          <template v-if="form.item_type === 'maintenance' && form.recurrence_mode === 'calendar'">
            <v-row>
              <v-col cols="12" sm="6">
                <v-text-field v-model.number="form.calendar_months" type="number" min="1" max="120" label="Alle … Monate" />
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="form.calendar_month"
                  clearable
                  label="Nur in diesem Monat (optional)"
                  :items="[
                    { title: 'Januar', value: 1 }, { title: 'Februar', value: 2 },
                    { title: 'März', value: 3 }, { title: 'April', value: 4 },
                    { title: 'Mai', value: 5 }, { title: 'Juni', value: 6 },
                    { title: 'Juli', value: 7 }, { title: 'August', value: 8 },
                    { title: 'September', value: 9 }, { title: 'Oktober', value: 10 },
                    { title: 'November', value: 11 }, { title: 'Dezember', value: 12 }
                  ]"
                />
              </v-col>
            </v-row>
            <v-checkbox v-model="form.calendar_last_day" label="Am letzten Kalendertag des Monats" />
            <v-text-field
              v-if="!form.calendar_last_day"
              v-model.number="form.calendar_day"
              type="number"
              min="1"
              max="31"
              label="Kalendertag"
              hint="Fehlt der Tag in einem Monat, wird dessen letzter Tag verwendet."
              persistent-hint
            />
          </template>
          <v-select
            v-model="form.priority"
            :items="[
              { title: 'Niedrig', value: 'low' },
              { title: 'Normal', value: 'normal' },
              { title: 'Hoch', value: 'high' }
            ]"
            label="Priorität"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="dialog = false">Abbrechen</v-btn>
          <v-btn color="primary" :disabled="!form.title.trim()" :loading="saving" @click="save">Speichern</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.maintenance-page {
  max-width: 1500px;
}
.metric {
  font-size: 2rem;
  font-weight: 700;
}
</style>
