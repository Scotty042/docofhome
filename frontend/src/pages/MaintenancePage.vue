<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { consumptionApi } from '../services/consumptionApi'
import { workItemsApi } from '../services/workItemsApi'
import type { ConsumptionReadingReminder } from '../types/consumption'
import type {
  RecurrenceMode,
  WorkHistory,
  WorkHistoryEntryWrite,
  WorkItemEvent,
  WorkItemRead,
  WorkItemType,
  WorkItemWrite,
  WorkPriority,
  WorkStatus,
  WorkSubjectRead,
  WorkSubjectType,
  WorkSummary
} from '../types/work'

const route = useRoute()
const router = useRouter()
const items = ref<WorkItemRead[]>([])
const subjects = ref<WorkSubjectRead[]>([])
const readingReminders = ref<ConsumptionReadingReminder[]>([])
const summary = ref<WorkSummary | null>(null)
const loading = ref(false)
const saving = ref(false)
const actionId = ref<string | null>(null)
const error = ref<string | null>(null)
const statusFilter = ref<WorkStatus | 'all'>('open')
const typeFilter = ref<WorkItemType | 'all'>('all')
const subjectFilter = ref<string | 'all'>('all')

const dialog = ref(false)
const editing = ref<WorkItemRead | null>(null)
const form = ref(emptyWorkForm())

const subjectDialog = ref(false)
const editingSubject = ref<WorkSubjectRead | null>(null)
const subjectForm = ref({ name: '', subject_type: 'general' as WorkSubjectType, description: '' })

const completionDialog = ref(false)
const completionItem = ref<WorkItemRead | null>(null)
const completionForm = ref(emptyHistoryForm(false))

const historyDialog = ref(false)
const historyLoading = ref(false)
const historyItem = ref<WorkItemRead | null>(null)
const history = ref<WorkHistory | null>(null)
const historyEntryDialog = ref(false)
const editingHistoryEntry = ref<WorkItemEvent | null>(null)
const historyForm = ref(emptyHistoryForm(true))

const attachmentDialog = ref(false)
const attachmentEvent = ref<WorkItemEvent | null>(null)
const attachmentFiles = ref<File[]>([])

function emptyWorkForm() {
  return {
    item_type: 'task' as WorkItemType,
    title: '',
    description: '',
    subject_id: null as string | null,
    due_at: '',
    recurrence_days: null as number | null,
    recurrence_mode: 'none' as RecurrenceMode,
    calendar_months: 1 as number | null,
    calendar_day: null as number | null,
    calendar_month: null as number | null,
    calendar_last_day: false,
    priority: 'normal' as WorkPriority
  }
}

function emptyHistoryForm(requireDate: boolean) {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
  return {
    occurred_at: requireDate ? local : '',
    note: '',
    cost_amount: null as number | null,
    cost_currency: 'EUR',
    reading_value: null as number | null,
    reading_unit: ''
  }
}

const filteredItems = computed(() => items.value.filter((item) => (
  (statusFilter.value === 'all' || item.status === statusFilter.value)
  && (typeFilter.value === 'all' || item.item_type === typeFilter.value)
  && (subjectFilter.value === 'all' || item.subject_id === subjectFilter.value)
)))

const subjectOptions = computed(() => subjects.value.map((subject) => ({
  title: `${subject.name} · ${subjectTypeLabel(subject.subject_type)}`,
  value: subject.id
})))

function toLocalInput(value: string | null): string {
  if (!value) return ''
  const date = new Date(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

function toIso(value: string): string | null {
  return value ? new Date(value).toISOString() : null
}

function historyPayload(source: ReturnType<typeof emptyHistoryForm>, requireDate: boolean): WorkHistoryEntryWrite {
  const occurredAt = toIso(source.occurred_at)
  if (requireDate && !occurredAt) throw new Error('Bitte ein Durchführungsdatum angeben.')
  return {
    occurred_at: occurredAt ?? new Date().toISOString(),
    note: source.note.trim() || null,
    cost_amount: source.cost_amount,
    cost_currency: source.cost_amount == null ? null : (source.cost_currency.trim().toUpperCase() || 'EUR'),
    reading_value: source.reading_value,
    reading_unit: source.reading_value == null ? null : (source.reading_unit.trim() || null)
  }
}

async function load() {
  loading.value = true
  error.value = null
  try {
    const [loadedItems, loadedSummary, loadedReadingReminders, loadedSubjects] = await Promise.all([
      workItemsApi.list(),
      workItemsApi.summary(),
      consumptionApi.readingReminders(31),
      workItemsApi.subjects()
    ])
    items.value = loadedItems
    summary.value = loadedSummary
    readingReminders.value = loadedReadingReminders
    subjects.value = loadedSubjects
    const requestedSubject = typeof route.query.subject === 'string' ? route.query.subject : null
    if (requestedSubject && loadedSubjects.some((subject) => subject.id === requestedSubject)) {
      subjectFilter.value = requestedSubject
    }
    const requestedHistory = typeof route.query.history === 'string' ? route.query.history : null
    const requestedItem = requestedHistory ? loadedItems.find((item) => item.id === requestedHistory) : null
    if (requestedItem && (!historyDialog.value || historyItem.value?.id !== requestedItem.id)) {
      void openHistory(requestedItem)
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Wartungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function chooseSubjectFilter(id: string | 'all') {
  subjectFilter.value = id
  void router.replace({ query: id === 'all' ? {} : { subject: id } })
}

function startCreate(subjectId: string | null = null) {
  editing.value = null
  form.value = emptyWorkForm()
  form.value.subject_id = subjectId
  dialog.value = true
}

function startEdit(item: WorkItemRead) {
  editing.value = item
  form.value = {
    item_type: item.item_type,
    title: item.title,
    description: item.description ?? '',
    subject_id: item.subject_id,
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
    subject_id: editing.value?.target_id ? null : form.value.subject_id,
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

function startComplete(item: WorkItemRead) {
  completionItem.value = item
  completionForm.value = emptyHistoryForm(false)
  completionDialog.value = true
}

async function completeItem() {
  if (!completionItem.value) return
  saving.value = true
  error.value = null
  try {
    const payload = historyPayload(completionForm.value, false)
    await workItemsApi.complete(completionItem.value.id, {
      ...payload,
      occurred_at: completionForm.value.occurred_at ? payload.occurred_at : null
    })
    completionDialog.value = false
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Eintrag konnte nicht abgeschlossen werden.'
  } finally {
    saving.value = false
  }
}

async function act(item: WorkItemRead, action: 'cancel' | 'reopen' | 'delete') {
  actionId.value = item.id
  error.value = null
  try {
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

function startSubjectCreate() {
  editingSubject.value = null
  subjectForm.value = { name: '', subject_type: 'general', description: '' }
  subjectDialog.value = true
}

function startSubjectEdit(subject: WorkSubjectRead) {
  editingSubject.value = subject
  subjectForm.value = {
    name: subject.name,
    subject_type: subject.subject_type,
    description: subject.description ?? ''
  }
  subjectDialog.value = true
}

async function saveSubject() {
  if (!subjectForm.value.name.trim()) return
  saving.value = true
  error.value = null
  try {
    const payload = {
      name: subjectForm.value.name.trim(),
      subject_type: subjectForm.value.subject_type,
      description: subjectForm.value.description.trim() || null
    }
    if (editingSubject.value) await workItemsApi.updateSubject(editingSubject.value.id, payload)
    else await workItemsApi.createSubject(payload)
    subjectDialog.value = false
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Bezugsobjekt konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function deleteSubject(subject: WorkSubjectRead) {
  error.value = null
  try {
    await workItemsApi.removeSubject(subject.id)
    if (subjectFilter.value === subject.id) chooseSubjectFilter('all')
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Bezugsobjekt konnte nicht gelöscht werden.'
  }
}

async function openHistory(item: WorkItemRead) {
  historyItem.value = item
  historyDialog.value = true
  historyLoading.value = true
  error.value = null
  try {
    history.value = await workItemsApi.history(item.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Historie konnte nicht geladen werden.'
  } finally {
    historyLoading.value = false
  }
}

function startHistoryCreate() {
  editingHistoryEntry.value = null
  historyForm.value = emptyHistoryForm(true)
  historyEntryDialog.value = true
}

function startHistoryEdit(event: WorkItemEvent) {
  editingHistoryEntry.value = event
  historyForm.value = {
    occurred_at: toLocalInput(event.occurred_at),
    note: event.note ?? '',
    cost_amount: event.cost_amount,
    cost_currency: event.cost_currency ?? 'EUR',
    reading_value: event.reading_value,
    reading_unit: event.reading_unit ?? ''
  }
  historyEntryDialog.value = true
}

async function saveHistory() {
  if (!historyItem.value) return
  saving.value = true
  error.value = null
  try {
    const payload = historyPayload(historyForm.value, true)
    if (editingHistoryEntry.value) {
      await workItemsApi.updateHistory(historyItem.value.id, editingHistoryEntry.value.id, payload)
    } else {
      await workItemsApi.addHistory(historyItem.value.id, payload)
    }
    historyEntryDialog.value = false
    await openHistory(historyItem.value)
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Historieneintrag konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function deleteHistory(event: WorkItemEvent) {
  if (!historyItem.value) return
  error.value = null
  try {
    await workItemsApi.removeHistory(historyItem.value.id, event.id)
    await openHistory(historyItem.value)
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Historieneintrag konnte nicht gelöscht werden.'
  }
}

function startAttachment(event: WorkItemEvent) {
  attachmentEvent.value = event
  attachmentFiles.value = []
  attachmentDialog.value = true
}

async function uploadAttachment() {
  const file = attachmentFiles.value[0]
  if (!historyItem.value || !attachmentEvent.value || !file) return
  saving.value = true
  error.value = null
  try {
    await workItemsApi.addAttachment(historyItem.value.id, attachmentEvent.value.id, file)
    attachmentDialog.value = false
    await openHistory(historyItem.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Anhang konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function deleteAttachment(event: WorkItemEvent, attachmentId: string) {
  if (!historyItem.value) return
  error.value = null
  try {
    await workItemsApi.removeAttachment(historyItem.value.id, event.id, attachmentId)
    await openHistory(historyItem.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Anhang konnte nicht gelöscht werden.'
  }
}

function statusLabel(status: WorkStatus): string {
  return { open: 'Offen', completed: 'Erledigt', cancelled: 'Abgebrochen' }[status]
}

function typeLabel(type: WorkItemType): string {
  return type === 'maintenance' ? 'Wartung' : 'Aufgabe'
}

function subjectTypeLabel(type: WorkSubjectType | null): string {
  if (!type) return 'Allgemein'
  return {
    device: 'Gerät', animal: 'Tier', vehicle: 'Fahrzeug', building: 'Gebäude', room: 'Raum',
    installation: 'Anlage/Installation', general: 'Allgemein', other: 'Sonstiges'
  }[type]
}

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleDateString() : '–'
}

onMounted(() => void load())
</script>

<template>
  <v-container class="maintenance-page pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-5">
      <div>
        <h1>Wartung & Aufgaben</h1>
        <p class="text-medium-emphasis mb-0">Fälligkeiten, wiederkehrende Tätigkeiten und ihre komplette Durchführungshistorie.</p>
      </div>
      <div class="d-flex ga-2">
        <v-btn variant="tonal" prepend-icon="mdi-tag-multiple-outline" @click="startSubjectCreate">Bezugsobjekt</v-btn>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="startCreate()">Neuer Eintrag</v-btn>
      </div>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <v-row class="mb-2">
      <v-col cols="6" md="3"><v-card title="Offen"><v-card-text class="metric">{{ summary?.open_total ?? '…' }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Überfällig"><v-card-text class="metric text-error">{{ summary?.overdue ?? '…' }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Nächste 7 Tage"><v-card-text class="metric">{{ summary?.due_next_7_days ?? '…' }}</v-card-text></v-card></v-col>
      <v-col cols="6" md="3"><v-card title="Erledigt"><v-card-text class="metric">{{ summary?.completed_total ?? '…' }}</v-card-text></v-card></v-col>
    </v-row>

    <v-card v-if="subjects.length" class="mb-4" title="Bezugsobjekte" prepend-icon="mdi-tag-multiple-outline">
      <v-card-text class="d-flex flex-wrap ga-2">
        <v-chip :variant="subjectFilter === 'all' ? 'flat' : 'tonal'" :color="subjectFilter === 'all' ? 'primary' : undefined" @click="chooseSubjectFilter('all')">Alle</v-chip>
        <div v-for="subject in subjects" :key="subject.id" class="d-flex align-center ga-1">
          <v-chip
            :variant="subjectFilter === subject.id ? 'flat' : 'tonal'"
            :color="subjectFilter === subject.id ? 'primary' : undefined"
            @click="chooseSubjectFilter(subject.id)"
          >
            {{ subject.name }} · {{ subjectTypeLabel(subject.subject_type) }}
            <span class="ml-1 text-medium-emphasis">({{ subject.activity_count }})</span>
          </v-chip>
          <v-menu>
            <template #activator="{ props }">
              <v-btn v-bind="props" icon="mdi-dots-vertical" size="x-small" variant="text" :aria-label="`${subject.name} verwalten`" />
            </template>
            <v-list density="compact">
              <v-list-item prepend-icon="mdi-plus" title="Tätigkeit hinzufügen" @click="startCreate(subject.id)" />
              <v-list-item prepend-icon="mdi-pencil" title="Bearbeiten" @click="startSubjectEdit(subject)" />
              <v-list-item prepend-icon="mdi-delete-outline" title="Löschen" @click="deleteSubject(subject)" />
            </v-list>
          </v-menu>
        </div>
      </v-card-text>
    </v-card>

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
      <v-card-text v-else-if="!loading && !error" class="text-medium-emphasis">Aktuell ist keine Zählerablesung fällig. Berücksichtigt werden monatliche Ablesepläne und die globale Fälligkeit nach der letzten Ablesung.</v-card-text>
    </v-card>

    <v-card>
      <v-card-text class="d-flex flex-wrap ga-3">
        <v-select v-model="statusFilter" :items="[{ title: 'Alle Status', value: 'all' }, { title: 'Offen', value: 'open' }, { title: 'Erledigt', value: 'completed' }, { title: 'Abgebrochen', value: 'cancelled' }]" label="Status" density="compact" hide-details max-width="220" />
        <v-select v-model="typeFilter" :items="[{ title: 'Alle Typen', value: 'all' }, { title: 'Aufgaben', value: 'task' }, { title: 'Wartungen', value: 'maintenance' }]" label="Typ" density="compact" hide-details max-width="220" />
        <v-select v-model="subjectFilter" :items="[{ title: 'Alle Bezugsobjekte', value: 'all' }, ...subjectOptions]" label="Bezugsobjekt" density="compact" hide-details clearable max-width="300" @update:model-value="(value) => chooseSubjectFilter(value || 'all')" />
      </v-card-text>
      <v-list v-if="filteredItems.length" lines="three">
        <v-list-item v-for="item in filteredItems" :key="item.id" :prepend-icon="item.item_type === 'maintenance' ? 'mdi-wrench-clock' : 'mdi-check-circle-outline'">
          <v-list-item-title class="d-flex flex-wrap align-center ga-2">
            <span>{{ item.title }}</span>
            <v-chip size="x-small" variant="tonal">{{ typeLabel(item.item_type) }}</v-chip>
            <v-chip v-if="item.generated" size="x-small" color="info" variant="tonal">Automatisch</v-chip>
            <v-chip size="x-small" :color="item.overdue ? 'error' : undefined" variant="tonal">{{ statusLabel(item.status) }}</v-chip>
          </v-list-item-title>
          <v-list-item-subtitle>
            <div v-if="item.subject_name"><v-icon size="small" icon="mdi-tag-outline" /> {{ item.subject_name }} · {{ subjectTypeLabel(item.subject_type) }}</div>
            <div v-else-if="item.target_label"><router-link v-if="item.target_route" :to="item.target_route">{{ item.target_label }}</router-link><span v-else>{{ item.target_label }}</span></div>
            <div :class="item.overdue ? 'text-error font-weight-bold' : ''">
              {{ item.due_at ? new Date(item.due_at).toLocaleString() : 'Keine Fälligkeit' }}
              <span v-if="item.recurrence_days"> · alle {{ item.recurrence_days }} Tage</span>
            </div>
            <div v-if="item.history_count">Zuletzt durchgeführt: {{ formatDate(item.last_performed_at) }} · {{ item.history_count }} Historieneinträge</div>
            <div v-if="item.description" class="text-truncate">{{ item.description }}</div>
          </v-list-item-subtitle>
          <template #append>
            <div class="d-flex flex-wrap ga-1">
              <v-btn icon="mdi-history" size="small" variant="tonal" aria-label="Historie" @click="openHistory(item)" />
              <v-btn v-if="item.generated && item.target_route && item.status === 'open'" icon="mdi-counter" size="small" color="primary" variant="tonal" aria-label="Zähler ablesen" :to="item.target_route" />
              <v-btn v-if="item.status === 'open' && !item.generated" icon="mdi-pencil" size="small" variant="text" aria-label="Bearbeiten" @click="startEdit(item)" />
              <v-btn v-if="item.status === 'open' && !item.generated" icon="mdi-check" size="small" color="success" variant="tonal" :loading="actionId === item.id" aria-label="Erledigen" @click="startComplete(item)" />
              <v-btn v-if="item.status === 'open' && !item.generated" icon="mdi-close" size="small" variant="text" aria-label="Abbrechen" @click="act(item, 'cancel')" />
              <v-btn v-else-if="!item.generated" icon="mdi-refresh" size="small" variant="text" aria-label="Wieder öffnen" @click="act(item, 'reopen')" />
              <v-btn v-if="!item.generated" icon="mdi-delete-outline" size="small" color="error" variant="text" aria-label="Löschen" @click="act(item, 'delete')" />
            </div>
          </template>
        </v-list-item>
      </v-list>
      <v-card-text v-else class="text-medium-emphasis">Keine passenden Einträge vorhanden.</v-card-text>
    </v-card>

    <v-dialog v-model="dialog" max-width="760">
      <v-card :title="editing ? 'Eintrag bearbeiten' : 'Eintrag anlegen'" prepend-icon="mdi-format-list-checks">
        <v-card-text>
          <v-select v-model="form.item_type" :items="[{ title: 'Aufgabe', value: 'task' }, { title: 'Wartung / wiederkehrende Tätigkeit', value: 'maintenance' }]" label="Typ" />
          <v-text-field v-model="form.title" label="Tätigkeit / Titel" maxlength="200" counter autofocus />
          <v-autocomplete v-if="!editing?.target_id" v-model="form.subject_id" :items="subjectOptions" label="Bezugsobjekt (optional)" clearable hint="z. B. Penny, Kühlschrank, Auto, Badezimmer" persistent-hint />
          <v-alert v-else type="info" variant="tonal" density="compact" class="mb-3">Dieser bestehende Eintrag bleibt mit {{ editing.target_label }} verknüpft.</v-alert>
          <v-textarea v-model="form.description" label="Beschreibung" rows="4" />
          <v-text-field v-model="form.due_at" label="Fällig am" type="datetime-local" />
          <v-select v-if="form.item_type === 'maintenance'" v-model="form.recurrence_mode" :items="[{ title: 'Keine Wiederholung', value: 'none' }, { title: 'Festes Tagesintervall', value: 'interval' }, { title: 'Kalenderregel', value: 'calendar' }]" label="Wiederholung" />
          <v-text-field v-if="form.item_type === 'maintenance' && form.recurrence_mode === 'interval'" v-model.number="form.recurrence_days" label="Wiederholung in Tagen" type="number" min="1" max="3650" clearable />
          <template v-if="form.item_type === 'maintenance' && form.recurrence_mode === 'calendar'">
            <v-row>
              <v-col cols="12" sm="6"><v-select v-model="form.calendar_months" :items="[1, 2, 3, 6, 12]" label="Alle … Monate" /></v-col>
              <v-col cols="12" sm="6"><v-select v-model="form.calendar_month" clearable label="Nur in diesem Monat (optional)" :items="[{ title: 'Januar', value: 1 }, { title: 'Februar', value: 2 }, { title: 'März', value: 3 }, { title: 'April', value: 4 }, { title: 'Mai', value: 5 }, { title: 'Juni', value: 6 }, { title: 'Juli', value: 7 }, { title: 'August', value: 8 }, { title: 'September', value: 9 }, { title: 'Oktober', value: 10 }, { title: 'November', value: 11 }, { title: 'Dezember', value: 12 }]" /></v-col>
            </v-row>
            <v-checkbox v-model="form.calendar_last_day" label="Am letzten Kalendertag des Monats" />
            <v-text-field v-if="!form.calendar_last_day" v-model.number="form.calendar_day" type="number" min="1" max="31" label="Kalendertag" />
          </template>
          <v-select v-model="form.priority" :items="[{ title: 'Niedrig', value: 'low' }, { title: 'Normal', value: 'normal' }, { title: 'Hoch', value: 'high' }]" label="Priorität" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="dialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!form.title.trim()" :loading="saving" @click="save">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="subjectDialog" max-width="650">
      <v-card :title="editingSubject ? 'Bezugsobjekt bearbeiten' : 'Bezugsobjekt anlegen'" prepend-icon="mdi-tag-outline">
        <v-card-text>
          <v-text-field v-model="subjectForm.name" label="Name" placeholder="z. B. Penny" autofocus />
          <v-select v-model="subjectForm.subject_type" :items="[{ title: 'Gerät', value: 'device' }, { title: 'Tier', value: 'animal' }, { title: 'Fahrzeug', value: 'vehicle' }, { title: 'Gebäude', value: 'building' }, { title: 'Raum', value: 'room' }, { title: 'Anlage / Installation', value: 'installation' }, { title: 'Allgemein', value: 'general' }, { title: 'Sonstiges', value: 'other' }]" label="Art" />
          <v-textarea v-model="subjectForm.description" label="Beschreibung (optional)" rows="3" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="subjectDialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!subjectForm.name.trim()" :loading="saving" @click="saveSubject">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="completionDialog" max-width="680">
      <v-card :title="`${completionItem?.title ?? 'Eintrag'} als durchgeführt markieren`" prepend-icon="mdi-check-circle-outline">
        <v-card-text>
          <v-text-field v-model="completionForm.occurred_at" type="datetime-local" label="Durchgeführt am (leer = jetzt)" />
          <v-textarea v-model="completionForm.note" label="Notiz (optional)" rows="3" />
          <v-row><v-col cols="8"><v-text-field v-model.number="completionForm.cost_amount" type="number" min="0" step="0.01" label="Kosten (optional)" /></v-col><v-col cols="4"><v-text-field v-model="completionForm.cost_currency" label="Währung" maxlength="3" /></v-col></v-row>
          <v-row><v-col cols="8"><v-text-field v-model.number="completionForm.reading_value" type="number" label="Mess-/Zählerwert (optional)" /></v-col><v-col cols="4"><v-text-field v-model="completionForm.reading_unit" label="Einheit" placeholder="km, h, kWh …" /></v-col></v-row>
          <v-alert type="info" variant="tonal" density="compact">Die Durchführung wird automatisch in der Historie gespeichert.</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="completionDialog = false">Abbrechen</v-btn><v-btn color="success" :loading="saving" @click="completeItem">Durchgeführt</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="historyDialog" max-width="980">
      <v-card :title="`Historie · ${historyItem?.title ?? ''}`" prepend-icon="mdi-history">
        <template #append><v-btn v-if="historyItem && !historyItem.generated" size="small" color="primary" prepend-icon="mdi-plus" @click="startHistoryCreate">Vergangene Durchführung</v-btn></template>
        <v-progress-linear v-if="historyLoading" indeterminate />
        <v-card-text v-if="history">
          <div v-if="historyItem?.subject_name" class="mb-3 text-medium-emphasis">Bezugsobjekt: <strong>{{ historyItem.subject_name }}</strong></div>
          <v-row class="mb-4">
            <v-col cols="6" md="3"><v-sheet border rounded class="pa-3"><div class="text-caption">Durchführungen</div><div class="history-metric">{{ history.stats.count }}</div></v-sheet></v-col>
            <v-col cols="6" md="3"><v-sheet border rounded class="pa-3"><div class="text-caption">Letzter Abstand</div><div class="history-metric">{{ history.stats.last_interval_days == null ? '–' : `${history.stats.last_interval_days} T.` }}</div></v-sheet></v-col>
            <v-col cols="6" md="3"><v-sheet border rounded class="pa-3"><div class="text-caption">Ø Abstand</div><div class="history-metric">{{ history.stats.average_interval_days == null ? '–' : `${history.stats.average_interval_days} T.` }}</div></v-sheet></v-col>
            <v-col cols="6" md="3"><v-sheet border rounded class="pa-3"><div class="text-caption">Min. / Max.</div><div class="history-metric small">{{ history.stats.shortest_interval_days ?? '–' }} / {{ history.stats.longest_interval_days ?? '–' }} T.</div></v-sheet></v-col>
          </v-row>

          <v-timeline v-if="history.entries.length" side="end" density="compact">
            <v-timeline-item v-for="event in history.entries" :key="event.id" dot-color="primary" size="small">
              <div class="d-flex flex-wrap justify-space-between ga-2">
                <div>
                  <div class="font-weight-bold">{{ new Date(event.occurred_at).toLocaleString() }}</div>
                  <div v-if="event.interval_days != null" class="text-medium-emphasis">{{ event.interval_days }} Tage seit der vorherigen Durchführung</div>
                  <div v-if="event.note" class="mt-1">{{ event.note }}</div>
                  <div v-if="event.cost_amount != null" class="text-medium-emphasis">Kosten: {{ event.cost_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }} {{ event.cost_currency }}</div>
                  <div v-if="event.reading_value != null" class="text-medium-emphasis">Messwert: {{ event.reading_value }} {{ event.reading_unit ?? '' }}</div>
                  <div v-if="event.attachments.length" class="d-flex flex-wrap ga-1 mt-2">
                    <v-chip v-for="attachment in event.attachments" :key="attachment.id" size="small" prepend-icon="mdi-paperclip" :href="workItemsApi.attachmentUrl(historyItem?.id ?? '', event.id, attachment.id)" target="_blank">
                      {{ attachment.file_name }}
                      <v-icon v-if="!historyItem?.generated" end icon="mdi-close" @click.prevent.stop="deleteAttachment(event, attachment.id)" />
                    </v-chip>
                  </div>
                </div>
                <div v-if="!historyItem?.generated" class="d-flex ga-1">
                  <v-btn icon="mdi-paperclip" size="x-small" variant="text" aria-label="Anhang hinzufügen" @click="startAttachment(event)" />
                  <v-btn icon="mdi-pencil" size="x-small" variant="text" aria-label="Historieneintrag bearbeiten" @click="startHistoryEdit(event)" />
                  <v-btn icon="mdi-delete-outline" size="x-small" color="error" variant="text" aria-label="Historieneintrag löschen" @click="deleteHistory(event)" />
                </div>
              </div>
            </v-timeline-item>
          </v-timeline>
          <v-alert v-else type="info" variant="tonal">Noch keine Durchführung dokumentiert. Über „Vergangene Durchführung“ können auch ältere Termine nachgetragen werden.</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="historyDialog = false">Schließen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="historyEntryDialog" max-width="680">
      <v-card :title="editingHistoryEntry ? 'Historieneintrag bearbeiten' : 'Vergangene Durchführung hinzufügen'" prepend-icon="mdi-history">
        <v-card-text>
          <v-text-field v-model="historyForm.occurred_at" type="datetime-local" label="Durchgeführt am" />
          <v-textarea v-model="historyForm.note" label="Notiz (optional)" rows="3" />
          <v-row><v-col cols="8"><v-text-field v-model.number="historyForm.cost_amount" type="number" min="0" step="0.01" label="Kosten (optional)" /></v-col><v-col cols="4"><v-text-field v-model="historyForm.cost_currency" label="Währung" maxlength="3" /></v-col></v-row>
          <v-row><v-col cols="8"><v-text-field v-model.number="historyForm.reading_value" type="number" label="Mess-/Zählerwert (optional)" /></v-col><v-col cols="4"><v-text-field v-model="historyForm.reading_unit" label="Einheit" /></v-col></v-row>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="historyEntryDialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!historyForm.occurred_at" :loading="saving" @click="saveHistory">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="attachmentDialog" max-width="620">
      <v-card title="Anhang zur Durchführung" prepend-icon="mdi-paperclip">
        <v-card-text><v-file-input v-model="attachmentFiles" label="Datei oder Bild" show-size :rules="[(files) => !files || !files.length || files[0].size <= 20 * 1024 * 1024 || 'Maximal 20 MB']" /></v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="attachmentDialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!attachmentFiles.length" :loading="saving" @click="uploadAttachment">Hochladen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.maintenance-page { max-width: 1500px; }
.metric { font-size: 2rem; font-weight: 700; }
.history-metric { font-size: 1.45rem; font-weight: 700; }
.history-metric.small { font-size: 1.15rem; }
</style>
