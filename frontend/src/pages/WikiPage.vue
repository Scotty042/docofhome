<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { knowledgeApi } from '../services/knowledgeApi'
import type { WikiPageRead, WikiPageWrite } from '../types/knowledge'

const route = useRoute()
const router = useRouter()
const pages = ref<WikiPageRead[]>([])
const selected = ref<WikiPageRead | null>(null)
const loading = ref(false)
const saving = ref(false)
const archiving = ref(false)
const error = ref<string | null>(null)
const search = ref('')
const editorOpen = ref(false)
const archiveOpen = ref(false)
const editing = ref<WikiPageRead | null>(null)
const form = ref<WikiPageWrite>({
  title: '',
  content: '',
  parent_id: null,
  sort_order: 0
})

const archivedView = computed(() => route.query.archived === '1')
const selectedId = computed(() => {
  const value = route.query.page
  return typeof value === 'string' && value ? value : null
})
const parentOptions = computed(() => [
  { title: 'Keine übergeordnete Seite', value: null },
  ...pages.value
    .filter((page) => page.id !== editing.value?.id)
    .map((page) => ({ title: page.path, value: page.id }))
])

async function loadPages(preferredId: string | null = selectedId.value) {
  loading.value = true
  error.value = null
  try {
    const loadedPages = await knowledgeApi.wikiPages(search.value, archivedView.value)
    pages.value = archivedView.value
      ? loadedPages.filter((page) => page.archived)
      : loadedPages.filter((page) => !page.archived)
    const next = preferredId
      ? pages.value.find((page) => page.id === preferredId) ?? null
      : pages.value[0] ?? null
    selected.value = next
    if (next && selectedId.value !== next.id) {
      await router.replace({
        path: '/wiki',
        query: archivedView.value ? { page: next.id, archived: '1' } : { page: next.id }
      })
    } else if (!next && selectedId.value) {
      await router.replace({ path: '/wiki', query: archivedView.value ? { archived: '1' } : {} })
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Wiki-Seiten konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function selectPage(page: WikiPageRead) {
  selected.value = page
  await router.push({
    path: '/wiki',
    query: archivedView.value ? { page: page.id, archived: '1' } : { page: page.id }
  })
}

function startCreate(parent: WikiPageRead | null = selected.value) {
  editing.value = null
  form.value = {
    title: '',
    content: '',
    parent_id: parent?.id ?? null,
    sort_order: 0
  }
  editorOpen.value = true
}

function startEdit(page: WikiPageRead) {
  editing.value = page
  form.value = {
    title: page.title,
    content: page.content,
    parent_id: page.parent_id,
    sort_order: page.sort_order
  }
  editorOpen.value = true
}

async function savePage() {
  if (!form.value.title.trim()) return
  saving.value = true
  error.value = null
  try {
    const payload: WikiPageWrite = {
      title: form.value.title.trim(),
      content: form.value.content,
      parent_id: form.value.parent_id,
      sort_order: form.value.sort_order
    }
    const saved = editing.value
      ? await knowledgeApi.updateWikiPage(editing.value.id, payload)
      : await knowledgeApi.createWikiPage(payload)
    editorOpen.value = false
    await loadPages(saved.id)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Wiki-Seite konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function archivePage() {
  if (!selected.value) return
  archiving.value = true
  error.value = null
  try {
    await knowledgeApi.archiveWikiPage(selected.value.id)
    archiveOpen.value = false
    selected.value = null
    await router.replace({ path: '/wiki' })
    await loadPages(null)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Wiki-Seite konnte nicht archiviert werden.'
  } finally {
    archiving.value = false
  }
}

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(search, () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => void loadPages(selectedId.value), 250)
})
watch(selectedId, (id) => {
  selected.value = pages.value.find((page) => page.id === id) ?? null
})

watch(archivedView, () => {
  void loadPages(selectedId.value)
})

onMounted(() => void loadPages())
</script>

<template>
  <v-container class="wiki-page pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-5">
      <div>
        <h1>Wiki</h1>
        <p class="text-medium-emphasis mb-0">Dauerhaftes Wissen zu Haus, Technik und Abläufen sammeln.</p>
      </div>
      <v-btn v-if="!archivedView" color="primary" prepend-icon="mdi-plus" @click="startCreate(null)">
        Neue Hauptseite
      </v-btn>
      <v-btn v-else variant="tonal" prepend-icon="mdi-arrow-left" to="/archive">
        Zurück zum Archiv
      </v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" closable class="mb-4" @click:close="error = null">
      {{ error }}
    </v-alert>

    <v-alert v-if="archivedView" type="warning" variant="tonal" class="mb-4">
      Archivansicht: Wiki-Seiten sind hier nur lesbar. Eine Wiederherstellung wird erst mit einem
      gesicherten Konflikt- und Hierarchie-Workflow ergänzt.
    </v-alert>

    <v-row>
      <v-col cols="12" md="4" lg="3">
        <v-card :title="archivedView ? 'Archivierte Seiten' : 'Seiten'" prepend-icon="mdi-book-open-page-variant" height="100%">
          <v-card-text class="pb-2">
            <v-text-field
              v-model="search"
              label="Wiki durchsuchen"
              prepend-inner-icon="mdi-magnify"
              clearable
              density="compact"
              hide-details
            />
          </v-card-text>
          <v-progress-linear v-if="loading" indeterminate />
          <v-list v-if="pages.length" nav density="compact">
            <v-list-item
              v-for="page in pages"
              :key="page.id"
              :active="selected?.id === page.id"
              :style="{ paddingInlineStart: `${16 + page.depth * 20}px` }"
              :prepend-icon="page.archived ? 'mdi-archive-outline' : 'mdi-file-document-outline'"
              :title="page.title"
              :subtitle="page.depth ? page.path : undefined"
              @click="selectPage(page)"
            />
          </v-list>
          <v-card-text v-else-if="!loading" class="text-medium-emphasis">
            {{ search ? 'Keine passende Wiki-Seite gefunden.' : (archivedView ? 'Keine archivierte Wiki-Seite vorhanden.' : 'Noch keine Wiki-Seite vorhanden.') }}
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="8" lg="9">
        <v-card v-if="selected" height="100%">
          <v-card-title class="d-flex flex-wrap align-center justify-space-between ga-3">
            <div>
              <div class="text-h5">{{ selected.title }}</div>
              <div class="text-caption text-medium-emphasis">{{ selected.path }}</div>
            </div>
            <div v-if="!archivedView" class="d-flex flex-wrap ga-2">
              <v-btn variant="tonal" prepend-icon="mdi-plus" @click="startCreate(selected)">
                Unterseite
              </v-btn>
              <v-btn variant="tonal" prepend-icon="mdi-pencil" @click="startEdit(selected)">
                Bearbeiten
              </v-btn>
              <v-btn color="error" variant="text" prepend-icon="mdi-archive-outline" @click="archiveOpen = true">
                Archivieren
              </v-btn>
            </div>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <div v-if="selected.content.trim()" class="wiki-content">{{ selected.content }}</div>
            <v-alert v-else type="info" variant="tonal">
              {{ archivedView
                ? 'Diese archivierte Wiki-Seite enthält keinen Inhalt.'
                : 'Diese Wiki-Seite ist noch leer. Über „Bearbeiten“ kannst du Inhalt ergänzen.' }}
            </v-alert>
          </v-card-text>
          <v-card-text class="text-caption text-medium-emphasis pt-0">
            Zuletzt geändert: {{ new Date(selected.updated_at).toLocaleString() }}
          </v-card-text>
        </v-card>
        <v-card v-else height="100%" class="d-flex align-center justify-center">
          <v-card-text class="text-center text-medium-emphasis py-12">
            <v-icon icon="mdi-book-open-page-variant" size="64" class="mb-4" />
            <div class="text-h6 mb-2">Wissen übersichtlich dokumentieren</div>
            <div>Lege eine erste Hauptseite an oder wähle links eine vorhandene Seite.</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>

  <v-dialog v-model="editorOpen" max-width="850" persistent>
    <v-card :title="editing ? 'Wiki-Seite bearbeiten' : 'Wiki-Seite anlegen'" prepend-icon="mdi-file-document-outline">
      <v-card-text>
        <v-text-field v-model="form.title" label="Titel" maxlength="200" counter autofocus />
        <v-select
          v-model="form.parent_id"
          :items="parentOptions"
          label="Übergeordnete Seite"
        />
        <v-textarea
          v-model="form.content"
          label="Inhalt"
          rows="14"
          maxlength="200000"
          counter
          hint="Absätze und Zeilenumbrüche bleiben erhalten."
          persistent-hint
        />
        <v-text-field
          v-model.number="form.sort_order"
          label="Sortierreihenfolge"
          type="number"
          min="0"
          max="100000"
        />
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="editorOpen = false">Abbrechen</v-btn>
        <v-btn color="primary" :disabled="!form.title.trim()" :loading="saving" @click="savePage">
          Speichern
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <v-dialog v-model="archiveOpen" max-width="520">
    <v-card title="Wiki-Seite archivieren" prepend-icon="mdi-archive-outline">
      <v-card-text>
        Die Seite „{{ selected?.title }}“ wird aus dem aktiven Wiki entfernt. Seiten mit aktiven
        Unterseiten können aus Sicherheitsgründen nicht archiviert werden.
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn @click="archiveOpen = false">Abbrechen</v-btn>
        <v-btn color="error" :loading="archiving" @click="archivePage">Archivieren</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.wiki-page {
  max-width: 1600px;
}

.wiki-content {
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  line-height: 1.65;
}
</style>
