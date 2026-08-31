<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'

import { consumptionApi } from '../services/consumptionApi'
import { paperlessApi } from '../services/paperlessApi'
import { workItemsApi } from '../services/workItemsApi'
import type { ConsumptionReadingReminder } from '../types/consumption'
import type { PaperlessDocument } from '../types/paperless'
import type {
  RecurrenceMode,
  WorkActivityKind,
  WorkHistory,
  WorkHistoryEntryWrite,
  WorkItemEvent,
  WorkItemRead,
  WorkItemType,
  WorkItemWrite,
  WorkPriority,
  WorkStatus,
  WorkSubjectRead,
  WorkSubjectTimeline,
  WorkSubjectType,
  WorkSummary
} from '../types/work'

const route = useRoute()
const router = useRouter()
const { smAndDown } = useDisplay()
const items = ref<WorkItemRead[]>([])
const subjects = ref<WorkSubjectRead[]>([])
const readingReminders = ref<ConsumptionReadingReminder[]>([])
const summary = ref<WorkSummary | null>(null)
const loading = ref(false)
const saving = ref(false)
const actionId = ref<string | null>(null)
const error = ref<string | null>(null)
const fieldErrors = ref<Record<string, string>>({})
const statusFilter = ref<WorkStatus | 'all'>('open')
const typeFilter = ref<WorkItemType | 'all'>('all')
const subjectFilter = ref<string | 'all'>('all')

const dialog = ref(false)
const editing = ref<WorkItemRead | null>(null)
const form = ref(emptyWorkForm())

const subjectDialog = ref(false)
const editingSubject = ref<WorkSubjectRead | null>(null)
const subjectForm = ref(emptySubjectForm())

const subjectTimelineDialog = ref(false)
const subjectTimelineLoading = ref(false)
const subjectTimeline = ref<WorkSubjectTimeline | null>(null)

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

const paperlessDialog = ref(false)
const paperlessEvent = ref<WorkItemEvent | null>(null)
const paperlessQuery = ref('')
const paperlessResults = ref<PaperlessDocument[]>([])
const paperlessLoading = ref(false)
const paperlessLinkingId = ref<number | null>(null)

function emptyWorkForm() {
  return {
    item_type: 'task' as WorkItemType,
    activity_kind: 'general' as WorkActivityKind,
    title: '',
    description: '',
    subject_id: null as string | null,
    due_at: '',
    recurrence_days: null as number | null,
    recurrence_mode: 'none' as RecurrenceMode,
    interval_value: 1 as number | null,
    interval_unit: 'months' as 'days' | 'weeks' | 'months' | 'years',
    calendar_months: 1 as number | null,
    calendar_day: null as number | null,
    calendar_month: null as number | null,
    calendar_last_day: false,
    priority: 'normal' as WorkPriority
  }
}

function emptySubjectForm() {
  return {
    name: '',
    subject_type: 'general' as WorkSubjectType,
    description: '',
    profile: {} as Record<string, string | number | boolean | null>
  }
}

type SubjectProfileField = { key: string; label: string; type?: 'text' | 'number' | 'date'; suffix?: string }

function subjectProfileFields(type: WorkSubjectType): SubjectProfileField[] {
  if (type === 'vehicle') return [
    { key: 'vehicle_kind', label: 'Fahrzeugart (PKW, Motorrad …)' },
    { key: 'manufacturer', label: 'Hersteller' },
    { key: 'model', label: 'Modell / Typ' },
    { key: 'license_plate', label: 'Kennzeichen' },
    { key: 'vin', label: 'FIN / Fahrzeug-Identifizierungsnummer' },
    { key: 'hsn', label: 'HSN (2.1)' },
    { key: 'tsn', label: 'TSN (2.2)' },
    { key: 'first_registration', label: 'Erstzulassung', type: 'date' },
    { key: 'fuel_type', label: 'Kraftstoff / Antriebsart' },
    { key: 'power_kw', label: 'Leistung', type: 'number', suffix: 'kW' },
    { key: 'displacement_cc', label: 'Hubraum', type: 'number', suffix: 'cm³' },
    { key: 'odometer_km', label: 'Aktueller Kilometerstand', type: 'number', suffix: 'km' }
  ]
  if (type === 'animal') return [
    { key: 'species', label: 'Tierart' },
    { key: 'breed', label: 'Rasse' },
    { key: 'birth_date', label: 'Geburtsdatum', type: 'date' },
    { key: 'chip_number', label: 'Chipnummer' },
    { key: 'insurance', label: 'Versicherung' },
    { key: 'weight_kg', label: 'Aktuelles Gewicht', type: 'number', suffix: 'kg' }
  ]
  if (type === 'installation') return [
    { key: 'manufacturer', label: 'Hersteller' },
    { key: 'model', label: 'Modell / Typ' },
    { key: 'serial_number', label: 'Seriennummer' },
    { key: 'installation_date', label: 'Einbau / Inbetriebnahme', type: 'date' },
    { key: 'energy_source', label: 'Energieträger / Betriebsart' },
    { key: 'location_notes', label: 'Standort / ergänzende Angaben' }
  ]
  if (type === 'device') return [
    { key: 'manufacturer', label: 'Hersteller' },
    { key: 'model', label: 'Modell / Typ' },
    { key: 'serial_number', label: 'Seriennummer' },
    { key: 'purchase_date', label: 'Kaufdatum', type: 'date' }
  ]
  return []
}

const activeSubjectProfileFields = computed(() => subjectProfileFields(subjectForm.value.subject_type))

function emptyHistoryForm(requireDate: boolean) {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
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

function toDateInput(value: string | null): string {
  if (!value) return ''
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  return match ? `${match[1]}-${match[2]}-${match[3]}` : ''
}

function dateToIso(value: string): string | null {
  return value ? `${value}T12:00:00.000Z` : null
}

function toIso(value: string): string | null {
  return value ? new Date(value).toISOString() : null
}

function historyPayload(source: ReturnType<typeof emptyHistoryForm>, requireDate: boolean): WorkHistoryEntryWrite {
  const occurredAt = dateToIso(source.occurred_at)
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
    activity_kind: item.activity_kind,
    title: item.title,
    description: item.description ?? '',
    subject_id: item.subject_id,
    due_at: toDateInput(item.due_at),
    recurrence_days: item.recurrence_days,
    recurrence_mode: item.recurrence_mode,
    interval_value: item.recurrence_mode === 'interval' ? item.recurrence_days : (item.calendar_months === 12 ? 1 : item.calendar_months),
    interval_unit: (item.recurrence_mode === 'interval' ? 'days' : (item.calendar_months === 12 ? 'years' : 'months')) as 'days' | 'weeks' | 'months' | 'years',
    calendar_months: item.calendar_months,
    calendar_day: item.calendar_day,
    calendar_month: item.calendar_month,
    calendar_last_day: item.calendar_last_day,
    priority: item.priority
  }
  dialog.value = true
}

async function save() {
  fieldErrors.value = {}
  if (!form.value.title.trim()) fieldErrors.value.title = 'Bitte eine Tätigkeit eingeben.'
  if (form.value.item_type === 'maintenance' && form.value.recurrence_mode !== 'none' && !form.value.interval_value) fieldErrors.value.recurrence = 'Bitte ein Wiederholungsintervall eingeben.'
  if (Object.keys(fieldErrors.value).length) return
  saving.value = true
  error.value = null
  const payload: WorkItemWrite = {
    item_type: form.value.item_type,
    activity_kind: form.value.activity_kind,
    title: form.value.title.trim(),
    description: form.value.description.trim() || null,
    target_type: editing.value?.target_type ?? null,
    target_id: editing.value?.target_id ?? null,
    subject_id: editing.value?.target_id ? null : form.value.subject_id,
    due_at: dateToIso(form.value.due_at),
    recurrence_days: form.value.item_type === 'maintenance' && form.value.recurrence_mode !== 'none' && ['days', 'weeks'].includes(form.value.interval_unit) ? (form.value.interval_value ?? 1) * (form.value.interval_unit === 'weeks' ? 7 : 1) : null,
    recurrence_mode: form.value.item_type !== 'maintenance' ? 'none' : form.value.recurrence_mode === 'none' ? 'none' : ['months', 'years'].includes(form.value.interval_unit) ? 'calendar' : 'interval',
    calendar_months: form.value.item_type === 'maintenance' && form.value.recurrence_mode !== 'none' && ['months', 'years'].includes(form.value.interval_unit) ? (form.value.interval_value ?? 1) * (form.value.interval_unit === 'years' ? 12 : 1) : null,
    calendar_day: form.value.item_type === 'maintenance' && form.value.recurrence_mode !== 'none' && ['months', 'years'].includes(form.value.interval_unit) ? 1 : null,
    calendar_month: null,
    calendar_last_day: false,
    priority: form.value.priority
  }
  try {
    if (editing.value) await workItemsApi.update(editing.value.id, payload)
    else await workItemsApi.create(payload)
    dialog.value = false
    await load()
  } catch (reason) {
    const message = reason instanceof Error ? reason.message : 'Eintrag konnte nicht gespeichert werden.'
    if (/Titel|Bezeichnung/i.test(message)) fieldErrors.value.title = message
    else if (/Wiederholung|Intervall|Kalender/i.test(message)) fieldErrors.value.recurrence = message
    else error.value = message
  } finally {
    saving.value = false
  }
}

function startComplete(item: WorkItemRead) {
  completionItem.value = item
  completionForm.value = emptyHistoryForm(false)
  completionDialog.value = true
}

async function completeToday(item: WorkItemRead) {
  actionId.value = item.id
  error.value = null
  try {
    await workItemsApi.complete(item.id, {
      occurred_at: dateToIso(new Date().toISOString().slice(0, 10)), note: null,
      cost_amount: null, cost_currency: null, reading_value: null, reading_unit: null
    })
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Durchführung konnte nicht gespeichert werden.'
  } finally {
    actionId.value = null
  }
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
  subjectForm.value = emptySubjectForm()
  subjectDialog.value = true
}

function startSubjectEdit(subject: WorkSubjectRead) {
  editingSubject.value = subject
  subjectForm.value = {
    name: subject.name,
    subject_type: subject.subject_type,
    description: subject.description ?? '',
    profile: { ...subject.profile }
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
      description: subjectForm.value.description.trim() || null,
      profile: Object.fromEntries(
        Object.entries(subjectForm.value.profile).filter(([, value]) => value !== '' && value !== null)
      )
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

async function openSubjectTimeline(subject: WorkSubjectRead) {
  subjectTimelineDialog.value = true
  subjectTimelineLoading.value = true
  error.value = null
  try {
    subjectTimeline.value = await workItemsApi.subjectTimeline(subject.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Zeitstrahl konnte nicht geladen werden.'
  } finally {
    subjectTimelineLoading.value = false
  }
}

function profileValueLabel(value: string | number | boolean | null): string {
  if (value === null || value === '') return '–'
  if (typeof value === 'boolean') return value ? 'Ja' : 'Nein'
  return String(value)
}

function profileKeyLabel(subject: WorkSubjectRead, key: string): string {
  return subjectProfileFields(subject.subject_type).find((field) => field.key === key)?.label ?? key
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
    occurred_at: toDateInput(event.occurred_at),
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

function startPaperlessLink(event: WorkItemEvent) {
  paperlessEvent.value = event
  paperlessQuery.value = ''
  paperlessResults.value = []
  paperlessDialog.value = true
  void searchPaperless()
}

async function searchPaperless() {
  paperlessLoading.value = true
  error.value = null
  try {
    paperlessResults.value = await paperlessApi.search(paperlessQuery.value, 30)
  } catch (reason) {
    paperlessResults.value = []
    error.value = reason instanceof Error ? reason.message : 'Paperless-Dokumente konnten nicht geladen werden.'
  } finally {
    paperlessLoading.value = false
  }
}

async function linkPaperless(document: PaperlessDocument) {
  if (!paperlessEvent.value || !historyItem.value) return
  paperlessLinkingId.value = document.document_id
  error.value = null
  try {
    await paperlessApi.link(paperlessEvent.value.id, document.document_id)
    paperlessDialog.value = false
    await openHistory(historyItem.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Paperless-Dokument konnte nicht verknüpft werden.'
  } finally {
    paperlessLinkingId.value = null
  }
}

async function unlinkPaperless(event: WorkItemEvent, linkId: string) {
  if (!historyItem.value) return
  error.value = null
  try {
    await paperlessApi.unlink(event.id, linkId)
    await openHistory(historyItem.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Paperless-Verknüpfung konnte nicht entfernt werden.'
  }
}

function activityKindLabel(kind: WorkActivityKind): string {
  return {
    general: 'Allgemein', maintenance: 'Wartung', inspection: 'Inspektion', repair: 'Reparatur',
    measurement: 'Messung', vaccination: 'Impfung', appointment: 'Termin',
    official_inspection: 'Prüfung / TÜV', chimney_sweep: 'Schornsteinfeger', service: 'Service', other: 'Sonstiges'
  }[kind]
}

function timelineIcon(kind: WorkActivityKind, entryType: string): string {
  if (entryType === 'due') return 'mdi-calendar-clock'
  return {
    general: 'mdi-history', maintenance: 'mdi-wrench', inspection: 'mdi-clipboard-check-outline', repair: 'mdi-tools',
    measurement: 'mdi-chart-line', vaccination: 'mdi-needle', appointment: 'mdi-calendar-account-outline',
    official_inspection: 'mdi-car-wrench', chimney_sweep: 'mdi-fireplace', service: 'mdi-wrench', other: 'mdi-circle-outline'
  }[kind]
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
  if (!value) return '–'
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})/)
  return match ? `${match[3]}.${match[2]}.${match[1]}` : '–'
}

function doneTodayLabel(item: WorkItemRead): string {
  return item.subject_type === 'animal' ? 'Heute gegeben' : 'Heute erledigt'
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
              <v-list-item prepend-icon="mdi-timeline-clock-outline" title="Zeitstrahl & Profil" @click="openSubjectTimeline(subject)" />
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
            <v-chip v-if="item.activity_kind !== 'general'" size="x-small" color="primary" variant="tonal">{{ activityKindLabel(item.activity_kind) }}</v-chip>
            <v-chip v-if="item.generated" size="x-small" color="info" variant="tonal">Automatisch</v-chip>
            <v-chip size="x-small" :color="item.overdue ? 'error' : undefined" variant="tonal">{{ statusLabel(item.status) }}</v-chip>
          </v-list-item-title>
          <v-list-item-subtitle>
            <div v-if="item.subject_name"><v-icon size="small" icon="mdi-tag-outline" /> {{ item.subject_name }} · {{ subjectTypeLabel(item.subject_type) }}</div>
            <div v-else-if="item.target_label"><router-link v-if="item.target_route" :to="item.target_route">{{ item.target_label }}</router-link><span v-else>{{ item.target_label }}</span></div>
            <div :class="item.overdue ? 'text-error font-weight-bold' : ''">
              {{ item.due_at ? `Nächster Termin: ${formatDate(item.due_at)}` : 'Noch keine Durchführung' }}
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
              <v-btn v-if="item.status === 'open' && !item.generated" size="small" color="success" variant="tonal" :loading="actionId === item.id" @click="completeToday(item)">{{ doneTodayLabel(item) }}</v-btn>
              <v-btn v-if="item.status === 'open' && !item.generated" size="small" variant="text" @click="startComplete(item)">Anderes Datum / Details</v-btn>
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
          <v-select v-model="form.activity_kind" :items="[
            { title: 'Allgemein', value: 'general' }, { title: 'Wartung', value: 'maintenance' },
            { title: 'Inspektion', value: 'inspection' }, { title: 'Reparatur', value: 'repair' },
            { title: 'Messung / Gewicht / Zählerstand', value: 'measurement' }, { title: 'Impfung', value: 'vaccination' },
            { title: 'Termin / Arzttermin', value: 'appointment' }, { title: 'Prüfung / TÜV', value: 'official_inspection' },
            { title: 'Schornsteinfeger', value: 'chimney_sweep' }, { title: 'Service', value: 'service' },
            { title: 'Sonstiges', value: 'other' }
          ]" label="Art der Tätigkeit" hint="Bestimmt die Darstellung im Zeitstrahl des Bezugsobjekts." persistent-hint />
          <v-text-field v-model="form.title" label="Tätigkeit / Titel" maxlength="200" counter autofocus :error-messages="fieldErrors.title" />
          <v-autocomplete v-if="!editing?.target_id" v-model="form.subject_id" :items="subjectOptions" label="Bezugsobjekt (optional)" clearable hint="z. B. Penny, Kühlschrank, Auto, Badezimmer" persistent-hint />
          <v-alert v-else type="info" variant="tonal" density="compact" class="mb-3">Dieser bestehende Eintrag bleibt mit {{ editing.target_label }} verknüpft.</v-alert>
          <v-textarea v-model="form.description" label="Beschreibung" rows="4" />
          <v-text-field v-model="form.due_at" label="Erster Termin (optional)" type="date" hint="Ohne Termin wird die nächste Fälligkeit nach der ersten Durchführung berechnet." persistent-hint />
          <v-select v-if="form.item_type === 'maintenance'" v-model="form.recurrence_mode" :items="[{ title: 'Keine feste Wiederholung', value: 'none' }, { title: 'Wiederkehrend', value: 'interval' }]" label="Wiederholung" />
          <v-row v-if="form.item_type === 'maintenance' && form.recurrence_mode !== 'none'">
            <v-col cols="5"><v-text-field v-model.number="form.interval_value" type="number" min="1" max="3650" label="Alle" :error-messages="fieldErrors.recurrence" /></v-col>
            <v-col cols="7"><v-select v-model="form.interval_unit" :items="[{ title: 'Tage', value: 'days' }, { title: 'Wochen', value: 'weeks' }, { title: 'Monate', value: 'months' }, { title: 'Jahre', value: 'years' }]" label="Einheit" /></v-col>
          </v-row>
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
          <v-alert v-if="activeSubjectProfileFields.length" type="info" variant="tonal" density="compact" class="mb-3">Die zusätzlichen Stammdaten gehören zum Bezugsobjekt und erscheinen in seiner Lebenslaufakte.</v-alert>
          <v-row v-if="activeSubjectProfileFields.length">
            <v-col v-for="field in activeSubjectProfileFields" :key="field.key" cols="12" md="6">
              <v-text-field
                v-model="subjectForm.profile[field.key]"
                :label="field.label"
                :type="field.type ?? 'text'"
                :suffix="field.suffix"
              />
            </v-col>
          </v-row>
          <v-textarea v-model="subjectForm.description" label="Beschreibung (optional)" rows="3" />
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="subjectDialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!subjectForm.name.trim()" :loading="saving" @click="saveSubject">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="completionDialog" max-width="680">
      <v-card :title="`${completionItem?.title ?? 'Eintrag'} als durchgeführt markieren`" prepend-icon="mdi-check-circle-outline">
        <v-card-text>
          <v-text-field v-model="completionForm.occurred_at" type="date" label="Durchgeführt am (leer = heute)" />
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
          <div class="history-summary mb-4">{{ history.stats.count }} Durchführungen<span v-if="history.stats.average_interval_days != null"> · durchschnittlicher Abstand {{ history.stats.average_interval_days }} Tage</span></div>

          <v-timeline v-if="history.entries.length" side="end" density="compact">
            <v-timeline-item v-for="event in history.entries" :key="event.id" dot-color="primary" size="small">
              <div class="d-flex flex-wrap justify-space-between ga-2">
                <div>
                  <div class="font-weight-bold">{{ formatDate(event.occurred_at) }}</div>
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
                  <div v-if="event.paperless_links.length" class="d-flex flex-wrap ga-1 mt-2">
                    <v-chip
                      v-for="link in event.paperless_links"
                      :key="link.id"
                      size="small"
                      prepend-icon="mdi-file-document-outline"
                      :href="link.source_url ?? undefined"
                      target="_blank"
                      color="info"
                      variant="tonal"
                    >
                      {{ link.title }}
                      <v-icon v-if="!historyItem?.generated" end icon="mdi-close" @click.prevent.stop="unlinkPaperless(event, link.id)" />
                    </v-chip>
                  </div>
                </div>
                <div v-if="!historyItem?.generated" class="d-flex ga-1">
                  <v-btn icon="mdi-paperclip" size="x-small" variant="text" aria-label="Lokalen Anhang hinzufügen" @click="startAttachment(event)" />
                  <v-btn icon="mdi-file-link-outline" size="x-small" variant="text" aria-label="Paperless-Dokument verknüpfen" @click="startPaperlessLink(event)" />
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
          <v-text-field v-model="historyForm.occurred_at" type="date" label="Durchgeführt am" />
          <v-textarea v-model="historyForm.note" label="Notiz (optional)" rows="3" />
          <v-row><v-col cols="8"><v-text-field v-model.number="historyForm.cost_amount" type="number" min="0" step="0.01" label="Kosten (optional)" /></v-col><v-col cols="4"><v-text-field v-model="historyForm.cost_currency" label="Währung" maxlength="3" /></v-col></v-row>
          <v-row><v-col cols="8"><v-text-field v-model.number="historyForm.reading_value" type="number" label="Mess-/Zählerwert (optional)" /></v-col><v-col cols="4"><v-text-field v-model="historyForm.reading_unit" label="Einheit" /></v-col></v-row>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="historyEntryDialog = false">Abbrechen</v-btn><v-btn color="primary" :disabled="!historyForm.occurred_at" :loading="saving" @click="saveHistory">Speichern</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="subjectTimelineDialog" max-width="1050" scrollable :fullscreen="smAndDown">
      <v-card class="timeline-dialog-card">
        <v-card-title class="timeline-dialog-header d-flex align-center ga-2">
          <v-icon icon="mdi-timeline-clock-outline" />
          <span class="text-truncate">Lebenslauf · {{ subjectTimeline?.subject.name ?? 'Bezugsobjekt' }}</span>
          <v-spacer />
          <v-btn icon="mdi-close" variant="text" aria-label="Lebenslauf schließen" @click="subjectTimelineDialog = false" />
        </v-card-title>
        <v-progress-linear v-if="subjectTimelineLoading" indeterminate />
        <v-card-text v-if="subjectTimeline">
          <div class="d-flex flex-wrap ga-2 mb-4">
            <v-chip variant="tonal">{{ subjectTypeLabel(subjectTimeline.subject.subject_type) }}</v-chip>
            <v-chip v-for="(value, key) in subjectTimeline.subject.profile" :key="key" size="small" variant="outlined">{{ profileKeyLabel(subjectTimeline.subject, String(key)) }}: {{ profileValueLabel(value) }}</v-chip>
          </div>
          <p v-if="subjectTimeline.subject.description" class="text-medium-emphasis mb-5">{{ subjectTimeline.subject.description }}</p>
          <v-timeline v-if="subjectTimeline.entries.length" side="end" density="compact">
            <v-timeline-item
              v-for="entry in subjectTimeline.entries"
              :key="entry.id"
              :icon="timelineIcon(entry.activity_kind, entry.entry_type)"
              :dot-color="entry.entry_type === 'due' ? 'warning' : 'primary'"
              size="small"
            >
              <div class="d-flex flex-wrap align-center ga-2">
                <strong>{{ formatDate(entry.at) }}</strong>
                <v-chip size="x-small" :color="entry.entry_type === 'due' ? 'warning' : 'primary'" variant="tonal">{{ entry.entry_type === 'due' ? 'Fällig' : activityKindLabel(entry.activity_kind) }}</v-chip>
              </div>
              <div class="font-weight-medium mt-1">{{ entry.title }}</div>
              <div v-if="entry.note" class="mt-1">{{ entry.note }}</div>
              <div v-if="entry.reading_value != null" class="text-medium-emphasis">Messwert: {{ entry.reading_value }} {{ entry.reading_unit ?? '' }}</div>
              <div v-if="entry.cost_amount != null" class="text-medium-emphasis">Kosten: {{ entry.cost_amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }} {{ entry.cost_currency ?? 'EUR' }}</div>
              <div v-if="entry.paperless_links.length" class="d-flex flex-wrap ga-1 mt-2">
                <v-chip v-for="link in entry.paperless_links" :key="link.id" size="small" prepend-icon="mdi-file-document-outline" color="info" variant="tonal" :href="link.source_url ?? undefined" target="_blank">{{ link.title }}</v-chip>
              </div>
            </v-timeline-item>
          </v-timeline>
          <v-alert v-else type="info" variant="tonal">Noch keine historischen Einträge oder zukünftigen Fälligkeiten vorhanden.</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="subjectTimelineDialog = false">Schließen</v-btn></v-card-actions>
      </v-card>
    </v-dialog>

    <v-dialog v-model="paperlessDialog" max-width="900">
      <v-card title="Paperless-Dokument verknüpfen" prepend-icon="mdi-file-link-outline">
        <v-card-text>
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">DocOfHome speichert nur die Verknüpfung zum bestehenden Paperless-Dokument, keine PDF-Kopie.</v-alert>
          <div class="d-flex flex-column flex-sm-row ga-2 mb-4">
            <v-text-field
              v-model="paperlessQuery"
              label="Paperless durchsuchen"
              placeholder="z. B. Werkstatt, Tierarzt oder Schornsteinfeger"
              hint="Paperless-Volltextsuche in Dokumenttitel und -inhalt."
              persistent-hint
              clearable
              @keyup.enter="searchPaperless"
            />
            <v-btn color="primary" prepend-icon="mdi-magnify" :loading="paperlessLoading" @click="searchPaperless">Suchen</v-btn>
          </div>
          <v-list v-if="paperlessResults.length" lines="two" border rounded>
            <v-list-item v-for="document in paperlessResults" :key="document.document_id">
              <v-list-item-title>{{ document.title }}</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(document.created) }}<span v-if="document.original_file_name"> · {{ document.original_file_name }}</span></v-list-item-subtitle>
              <template #append>
                <v-btn variant="tonal" color="primary" :loading="paperlessLinkingId === document.document_id" @click="linkPaperless(document)">Verknüpfen</v-btn>
              </template>
            </v-list-item>
          </v-list>
          <v-alert v-else-if="!paperlessLoading" type="info" variant="tonal">Keine Dokumente gefunden. Wenn Paperless noch nicht eingerichtet ist, hinterlege unter Einstellungen die Server-URL und einen API-Token.</v-alert>
        </v-card-text>
        <v-card-actions><v-spacer /><v-btn @click="paperlessDialog = false">Schließen</v-btn></v-card-actions>
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
.history-summary { color: rgb(var(--v-theme-on-surface-variant)); font-size: .95rem; }
.timeline-dialog-header { flex: 0 0 auto; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
@media (max-width: 960px) {
  .timeline-dialog-card { height: 100%; }
  .timeline-dialog-header { position: sticky; top: 0; z-index: 2; background: rgb(var(--v-theme-surface)); }
}
</style>
