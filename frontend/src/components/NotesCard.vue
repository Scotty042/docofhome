<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { knowledgeApi } from '../services/knowledgeApi'
import type { DomainNote, KnowledgeTargetType } from '../types/knowledge'

const props = defineProps<{
  targetType: KnowledgeTargetType
  targetId: string
  readOnly?: boolean
}>()

const notes = ref<DomainNote[]>([])
const loading = ref(false)
const saving = ref(false)
const deletingId = ref<string | null>(null)
const error = ref<string | null>(null)
const dialog = ref(false)
const editing = ref<DomainNote | null>(null)
const content = ref('')

async function loadNotes() {
  loading.value = true
  error.value = null
  try {
    notes.value = await knowledgeApi.notes(props.targetType, props.targetId)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Notizen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

function startCreate() {
  editing.value = null
  content.value = ''
  dialog.value = true
}

function startEdit(note: DomainNote) {
  editing.value = note
  content.value = note.content
  dialog.value = true
}

async function saveNote() {
  const normalized = content.value.trim()
  if (!normalized) return
  saving.value = true
  error.value = null
  try {
    if (editing.value) await knowledgeApi.updateNote(editing.value.id, normalized)
    else await knowledgeApi.createNote(props.targetType, props.targetId, normalized)
    dialog.value = false
    await loadNotes()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Notiz konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function deleteNote(note: DomainNote) {
  deletingId.value = note.id
  error.value = null
  try {
    await knowledgeApi.deleteNote(note.id)
    await loadNotes()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Notiz konnte nicht gelöscht werden.'
  } finally {
    deletingId.value = null
  }
}

onMounted(() => void loadNotes())
watch(() => [props.targetType, props.targetId], () => void loadNotes())
</script>

<template>
  <v-card title="Notizen" prepend-icon="mdi-note-text-outline" class="mb-5">
    <template #append>
      <v-btn
        v-if="!readOnly"
        size="small"
        variant="tonal"
        prepend-icon="mdi-plus"
        @click="startCreate"
      >
        Notiz
      </v-btn>
    </template>
    <v-progress-linear v-if="loading" indeterminate />
    <v-alert v-if="error" type="error" variant="tonal" class="ma-4">{{ error }}</v-alert>
    <v-list v-if="notes.length" lines="three">
      <v-list-item v-for="note in notes" :key="note.id" prepend-icon="mdi-note-text-outline">
        <v-list-item-title class="note-content">{{ note.content }}</v-list-item-title>
        <v-list-item-subtitle>
          {{ new Date(note.updated_at).toLocaleString() }}
          <span v-if="note.updated_at !== note.created_at"> · bearbeitet</span>
        </v-list-item-subtitle>
        <template #append>
          <div v-if="!readOnly" class="d-flex ga-1">
            <v-btn
              icon="mdi-pencil"
              variant="text"
              size="small"
              aria-label="Notiz bearbeiten"
              @click="startEdit(note)"
            />
            <v-btn
              icon="mdi-delete-outline"
              variant="text"
              size="small"
              color="error"
              :loading="deletingId === note.id"
              aria-label="Notiz löschen"
              @click="deleteNote(note)"
            />
          </div>
        </template>
      </v-list-item>
    </v-list>
    <v-card-text v-else-if="!loading" class="text-medium-emphasis">
      Noch keine Notizen hinterlegt.
    </v-card-text>
  </v-card>

  <v-dialog v-model="dialog" max-width="640">
    <v-card :title="editing ? 'Notiz bearbeiten' : 'Notiz hinzufügen'" prepend-icon="mdi-note-text-outline">
      <v-card-text>
        <v-textarea
          v-model="content"
          label="Notiz"
          rows="7"
          maxlength="20000"
          counter
          autofocus
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="dialog = false">Abbrechen</v-btn>
        <v-btn color="primary" :disabled="!content.trim()" :loading="saving" @click="saveNote">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.note-content {
  white-space: pre-wrap;
}
</style>
