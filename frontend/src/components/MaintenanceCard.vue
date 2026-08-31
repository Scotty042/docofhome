<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { workItemsApi } from '../services/workItemsApi'
import type { KnowledgeTargetType } from '../types/knowledge'
import type { WorkItemRead, WorkItemType, WorkItemWrite, WorkPriority } from '../types/work'

const props = defineProps<{
  targetType: KnowledgeTargetType
  targetId: string
  readOnly?: boolean
}>()

const items = ref<WorkItemRead[]>([])
const loading = ref(false)
const saving = ref(false)
const completingId = ref<string | null>(null)
const error = ref<string | null>(null)
const dialog = ref(false)
const form = ref({
  item_type: 'maintenance' as WorkItemType,
  title: '',
  description: '',
  due_at: '',
  recurrence_days: null as number | null,
  priority: 'normal' as WorkPriority
})

const openItems = computed(() => items.value.filter((item) => item.status === 'open'))

function toIso(value: string): string | null {
  return value ? new Date(value).toISOString() : null
}

async function loadItems() {
  loading.value = true
  error.value = null
  try {
    items.value = await workItemsApi.list({
      targetType: props.targetType,
      targetId: props.targetId
    })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Wartungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function startCreate() {
  form.value = {
    item_type: 'maintenance',
    title: '',
    description: '',
    due_at: '',
    recurrence_days: null,
    priority: 'normal'
  }
  dialog.value = true
}

async function saveItem() {
  if (!form.value.title.trim()) return
  saving.value = true
  error.value = null
  const payload: WorkItemWrite = {
    item_type: form.value.item_type,
    activity_kind: form.value.item_type === 'maintenance' ? 'maintenance' : 'general',
    title: form.value.title.trim(),
    description: form.value.description.trim() || null,
    target_type: props.targetType,
    target_id: props.targetId,
    subject_id: null,
    due_at: toIso(form.value.due_at),
    recurrence_days: form.value.item_type === 'maintenance' ? form.value.recurrence_days : null,
    recurrence_mode: form.value.item_type === 'maintenance' && form.value.recurrence_days ? 'interval' : 'none',
    calendar_months: null,
    calendar_day: null,
    calendar_month: null,
    calendar_last_day: false,
    priority: form.value.priority
  }
  try {
    await workItemsApi.create(payload)
    dialog.value = false
    await loadItems()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Wartung konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function completeItem(item: WorkItemRead) {
  completingId.value = item.id
  error.value = null
  try {
    await workItemsApi.complete(item.id)
    await loadItems()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Eintrag konnte nicht abgeschlossen werden.'
  } finally {
    completingId.value = null
  }
}

function formatDue(item: WorkItemRead): string {
  if (!item.due_at) return 'Keine Fälligkeit'
  return new Date(item.due_at).toLocaleString()
}

onMounted(() => void loadItems())
watch(() => [props.targetType, props.targetId], () => void loadItems())
</script>

<template>
  <v-card title="Wartung & Aufgaben" prepend-icon="mdi-format-list-checks" class="mb-5">
    <template #append>
      <v-btn
        v-if="!readOnly"
        size="small"
        variant="tonal"
        prepend-icon="mdi-plus"
        @click="startCreate"
      >
        Eintrag
      </v-btn>
    </template>
    <v-progress-linear v-if="loading" indeterminate />
    <v-alert v-if="error" type="error" variant="tonal" class="ma-4">{{ error }}</v-alert>
    <v-list v-if="openItems.length" lines="three">
      <v-list-item
        v-for="item in openItems"
        :key="item.id"
        :prepend-icon="item.item_type === 'maintenance' ? 'mdi-format-list-checks' : 'mdi-check-circle-outline'"
      >
        <v-list-item-title>{{ item.title }}</v-list-item-title>
        <v-list-item-subtitle>
          <span :class="item.overdue ? 'text-error font-weight-bold' : ''">{{ formatDue(item) }}</span>
          <span v-if="item.recurrence_days"> · alle {{ item.recurrence_days }} Tage</span>
          <div v-if="item.history_count" class="text-medium-emphasis">
            Zuletzt durchgeführt: {{ item.last_performed_at ? new Date(item.last_performed_at).toLocaleDateString() : '–' }} · {{ item.history_count }} Einträge
          </div>
          <div v-if="item.description" class="text-truncate">{{ item.description }}</div>
        </v-list-item-subtitle>
        <template #append>
          <div class="d-flex ga-1">
          <v-btn
            icon="mdi-history"
            variant="text"
            size="small"
            aria-label="Historie öffnen"
            :to="{ path: '/maintenance', query: { history: item.id } }"
          />
          <v-btn
            v-if="!readOnly"
            icon="mdi-check"
            color="success"
            variant="tonal"
            size="small"
            :loading="completingId === item.id"
            aria-label="Eintrag abschließen"
            @click="completeItem(item)"
          />
          </div>
        </template>
      </v-list-item>
    </v-list>
    <v-card-text v-else-if="!loading" class="text-medium-emphasis">
      Keine offenen Wartungen oder Aufgaben für dieses Objekt.
    </v-card-text>
  </v-card>

  <v-dialog v-model="dialog" max-width="680">
    <v-card title="Wartung oder Aufgabe anlegen" prepend-icon="mdi-format-list-checks">
      <v-card-text>
        <v-select
          v-model="form.item_type"
          :items="[
            { title: 'Wartung', value: 'maintenance' },
            { title: 'Aufgabe', value: 'task' }
          ]"
          label="Typ"
        />
        <v-text-field v-model="form.title" label="Titel" maxlength="200" counter autofocus />
        <v-textarea v-model="form.description" label="Beschreibung" rows="4" />
        <v-text-field v-model="form.due_at" label="Fällig am" type="datetime-local" />
        <v-text-field
          v-if="form.item_type === 'maintenance'"
          v-model.number="form.recurrence_days"
          label="Wiederholung in Tagen"
          type="number"
          min="1"
          max="3650"
          clearable
        />
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
        <v-btn color="primary" :disabled="!form.title.trim()" :loading="saving" @click="saveItem">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
