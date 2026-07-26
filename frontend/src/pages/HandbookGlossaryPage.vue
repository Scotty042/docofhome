<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import {
  categoryTitle,
  filterHandbookEntries,
  glossaryLetter,
  glossaryLetters,
  handbookCategories,
  handbookEntries,
  handbookSections,
  sortGlossaryEntries,
  type HandbookCategoryId,
  type HandbookEntry
} from '../content/handbook'

const route = useRoute()
const router = useRouter()
const search = ref('')
const selectedCategory = ref<HandbookCategoryId | 'all'>('all')
const viewMode = ref<'handbook' | 'glossary'>('handbook')
const expandedSections = ref<string[]>(handbookSections.map((section) => section.id))
const mobileTocOpen = ref<number[]>([])

const categoryOptions = computed(() => [
  { title: 'Alle Bereiche', value: 'all' },
  ...handbookCategories.map((category) => ({ title: category.title, value: category.id }))
])

const filteredEntries = computed(() => filterHandbookEntries(
  handbookEntries,
  search.value,
  selectedCategory.value
))

const filteredSections = computed(() => handbookSections
  .filter((section) => selectedCategory.value === 'all' || section.category === selectedCategory.value)
  .map((section) => ({
    ...section,
    entries: filterHandbookEntries(section.entries, search.value, selectedCategory.value)
  }))
  .filter((section) => section.entries.length > 0))

const sortedGlossary = computed(() => sortGlossaryEntries(filteredEntries.value))
const availableLetters = computed(() => glossaryLetters(sortedGlossary.value))
const glossaryGroups = computed(() => availableLetters.value.map((letter) => ({
  letter,
  entries: sortedGlossary.value.filter((entry) => glossaryLetter(entry) === letter)
})))

const activeFilterLabel = computed(() => selectedCategory.value === 'all'
  ? 'Alle Bereiche'
  : categoryTitle(selectedCategory.value))

function entryAnchor(entry: HandbookEntry): string {
  return `begriff-${entry.id}`
}

function sectionForEntry(entry: HandbookEntry): string | undefined {
  return handbookSections.find((section) => section.entries.some((candidate) => candidate.id === entry.id))?.id
}

async function scrollToAnchor(anchor: string) {
  await nextTick()
  document.getElementById(anchor)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function openEntry(entry: HandbookEntry) {
  const sectionId = sectionForEntry(entry)
  viewMode.value = 'handbook'
  search.value = ''
  selectedCategory.value = 'all'
  if (sectionId && !expandedSections.value.includes(sectionId)) {
    expandedSections.value = [...expandedSections.value, sectionId]
  }
  const anchor = entryAnchor(entry)
  await router.replace({ path: '/wiki/handbuch', hash: `#${anchor}` })
  await scrollToAnchor(anchor)
}

async function openSection(sectionId: string) {
  viewMode.value = 'handbook'
  if (!expandedSections.value.includes(sectionId)) {
    expandedSections.value = [...expandedSections.value, sectionId]
  }
  await router.replace({ path: '/wiki/handbuch', hash: `#${sectionId}` })
  await scrollToAnchor(sectionId)
}

async function jumpToLetter(letter: string) {
  viewMode.value = 'glossary'
  const anchor = `glossar-${letter}`
  await router.replace({ path: '/wiki/handbuch', hash: `#${anchor}` })
  await scrollToAnchor(anchor)
}

function relatedEntry(term: string): HandbookEntry | undefined {
  const normalized = term.toLocaleLowerCase('de')
  return handbookEntries.find((entry) => (
    entry.term.toLocaleLowerCase('de') === normalized
    || entry.aliases?.some((alias) => alias.toLocaleLowerCase('de') === normalized)
  ))
}

async function openRelated(term: string) {
  const entry = relatedEntry(term)
  if (entry) await openEntry(entry)
}

function clearFilters() {
  search.value = ''
  selectedCategory.value = 'all'
}

function applyHash(hash: string) {
  const anchor = hash.replace(/^#/, '')
  if (!anchor) return
  if (anchor.startsWith('glossar-')) viewMode.value = 'glossary'
  if (anchor.startsWith('begriff-')) {
    const entryId = anchor.replace(/^begriff-/, '')
    const entry = handbookEntries.find((candidate) => candidate.id === entryId)
    const sectionId = entry ? sectionForEntry(entry) : undefined
    if (sectionId && !expandedSections.value.includes(sectionId)) {
      expandedSections.value = [...expandedSections.value, sectionId]
    }
  }
  void scrollToAnchor(anchor)
}

watch([search, selectedCategory], () => {
  if (search.value.trim()) {
    expandedSections.value = filteredSections.value.map((section) => section.id)
  }
})

watch(() => route.hash, applyHash)

onMounted(() => applyHash(route.hash))
</script>

<template>
  <v-container class="handbook-page pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-start justify-space-between ga-3 mb-4">
      <div>
        <div class="d-flex align-center ga-2 mb-1">
          <v-btn icon="mdi-arrow-left" variant="text" size="small" aria-label="Zum Wiki" to="/wiki" />
          <h1>Handbuch & Glossar</h1>
        </div>
        <p class="text-medium-emphasis mb-0">
          Verständliche Hilfe für die private Hausdokumentation – vollständig in DocOfHome enthalten und offline nutzbar.
        </p>
      </div>
      <v-btn-toggle v-model="viewMode" mandatory color="primary" variant="outlined" density="comfortable">
        <v-btn value="handbook" prepend-icon="mdi-book-open-page-variant">Handbuch</v-btn>
        <v-btn value="glossary" prepend-icon="mdi-format-list-bulleted">Glossar A–Z</v-btn>
      </v-btn-toggle>
    </div>

    <v-alert type="warning" variant="tonal" icon="mdi-alert-outline" class="mb-4">
      Änderungen an elektrischen Anlagen gehören in die Hände einer Elektrofachkraft. Dieses Handbuch unterstützt nur die Dokumentation und ersetzt keine Planung, Prüfung oder Sicherheitsberatung.
    </v-alert>

    <v-card class="search-card mb-4" variant="elevated">
      <v-card-text>
        <v-row align="center" dense>
          <v-col cols="12" md="7">
            <v-text-field
              v-model="search"
              label="Handbuch und Glossar durchsuchen"
              placeholder="z. B. Sammelschiene, VLAN, DHCP oder Zählerstand"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" md="5">
            <v-select
              v-model="selectedCategory"
              :items="categoryOptions"
              item-title="title"
              item-value="value"
              label="Bereich"
              prepend-inner-icon="mdi-filter-variant"
              hide-details
            />
          </v-col>
        </v-row>
        <div class="d-flex flex-wrap align-center ga-2 mt-3">
          <v-chip color="primary" variant="tonal">
            {{ filteredEntries.length }} Begriffe · {{ activeFilterLabel }}
          </v-chip>
          <v-btn v-if="search || selectedCategory !== 'all'" variant="text" size="small" @click="clearFilters">
            Filter zurücksetzen
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <v-expansion-panels v-model="mobileTocOpen" class="d-md-none mb-4">
      <v-expansion-panel>
        <v-expansion-panel-title>Inhaltsverzeichnis</v-expansion-panel-title>
        <v-expansion-panel-text>
          <v-list nav density="comfortable">
            <v-list-item
              v-for="section in handbookSections"
              :key="section.id"
              :prepend-icon="handbookCategories.find((category) => category.id === section.category)?.icon"
              :title="section.title"
              @click="openSection(section.id)"
            />
          </v-list>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <v-row>
      <v-col cols="12" md="3" lg="2" class="d-none d-md-block">
        <v-card class="toc-card" title="Inhaltsverzeichnis" prepend-icon="mdi-format-list-bulleted">
          <v-list nav density="compact">
            <v-list-item
              v-for="section in handbookSections"
              :key="section.id"
              :prepend-icon="handbookCategories.find((category) => category.id === section.category)?.icon"
              :title="section.title"
              @click="openSection(section.id)"
            />
          </v-list>
          <v-divider />
          <v-card-text class="text-caption text-medium-emphasis">
            Direkte Links funktionieren auch mit Ankern, zum Beispiel <code>/wiki/handbuch#begriff-sammelschiene</code>.
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="9" lg="10">
        <template v-if="filteredEntries.length">
          <v-expansion-panels
            v-if="viewMode === 'handbook'"
            v-model="expandedSections"
            multiple
            class="handbook-sections"
          >
            <v-expansion-panel
              v-for="section in filteredSections"
              :id="section.id"
              :key="section.id"
              :value="section.id"
            >
              <v-expansion-panel-title>
                <div class="d-flex align-center ga-3">
                  <v-icon :icon="handbookCategories.find((category) => category.id === section.category)?.icon" />
                  <div>
                    <div class="text-h6">{{ section.title }}</div>
                    <div class="text-caption text-medium-emphasis">{{ section.entries.length }} passende Begriffe</div>
                  </div>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <p class="text-medium-emphasis mb-5">{{ section.introduction }}</p>
                <article
                  v-for="entry in section.entries"
                  :id="entryAnchor(entry)"
                  :key="entry.id"
                  class="definition-card mb-4"
                >
                  <div class="d-flex flex-wrap align-start justify-space-between ga-2">
                    <div>
                      <h2 class="text-h6 mb-1">{{ entry.term }}</h2>
                      <div v-if="entry.aliases?.length" class="text-caption text-medium-emphasis">
                        Auch: {{ entry.aliases.join(', ') }}
                      </div>
                    </div>
                    <v-chip size="small" variant="tonal">{{ categoryTitle(entry.category) }}</v-chip>
                  </div>
                  <p class="font-weight-medium mt-3 mb-2">{{ entry.summary }}</p>
                  <p class="mb-0">{{ entry.details }}</p>
                  <v-alert v-if="entry.example" type="info" variant="tonal" density="compact" class="mt-3">
                    <strong>Beispiel:</strong> {{ entry.example }}
                  </v-alert>
                  <div v-if="entry.related?.length" class="d-flex flex-wrap align-center ga-2 mt-3">
                    <span class="text-caption text-medium-emphasis">Verwandte Begriffe:</span>
                    <v-chip
                      v-for="term in entry.related"
                      :key="term"
                      size="small"
                      :clickable="Boolean(relatedEntry(term))"
                      @click="openRelated(term)"
                    >
                      {{ term }}
                    </v-chip>
                  </div>
                  <v-btn
                    class="mt-3"
                    variant="text"
                    size="small"
                    prepend-icon="mdi-link-variant"
                    :href="`#${entryAnchor(entry)}`"
                    @click.prevent="openEntry(entry)"
                  >
                    Link zu diesem Begriff
                  </v-btn>
                </article>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>

          <template v-else>
            <v-card class="mb-4" variant="outlined">
              <v-card-text>
                <div class="text-subtitle-1 font-weight-bold mb-3">Sprungmarken</div>
                <div class="d-flex flex-wrap ga-2">
                  <v-btn
                    v-for="letter in availableLetters"
                    :key="letter"
                    size="small"
                    variant="tonal"
                    min-width="44"
                    @click="jumpToLetter(letter)"
                  >
                    {{ letter }}
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>

            <section v-for="group in glossaryGroups" :id="`glossar-${group.letter}`" :key="group.letter" class="glossary-group mb-6">
              <div class="d-flex align-center ga-3 mb-3">
                <div class="text-h4 font-weight-bold">{{ group.letter }}</div>
                <v-divider />
              </div>
              <v-card
                v-for="entry in group.entries"
                :key="entry.id"
                class="mb-3 glossary-card"
                variant="outlined"
                @click="openEntry(entry)"
              >
                <v-card-text>
                  <div class="d-flex flex-wrap justify-space-between ga-2">
                    <div>
                      <div class="text-h6">{{ entry.term }}</div>
                      <div v-if="entry.aliases?.length" class="text-caption text-medium-emphasis">
                        {{ entry.aliases.join(', ') }}
                      </div>
                    </div>
                    <v-chip size="small" variant="tonal">{{ categoryTitle(entry.category) }}</v-chip>
                  </div>
                  <p class="mb-0 mt-2">{{ entry.summary }}</p>
                  <div class="text-caption text-primary mt-2">Diesen Begriff im Handbuch öffnen</div>
                </v-card-text>
              </v-card>
            </section>
          </template>
        </template>

        <v-card v-else class="text-center" variant="outlined">
          <v-card-text class="py-12">
            <v-icon icon="mdi-magnify" size="56" class="mb-3" />
            <div class="text-h6 mb-2">Kein passender Begriff gefunden</div>
            <p class="text-medium-emphasis">Prüfe den Suchbegriff oder entferne den Kategorienfilter.</p>
            <v-btn color="primary" variant="tonal" @click="clearFilters">Filter zurücksetzen</v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.handbook-page {
  max-width: 1700px;
}

.search-card {
  position: sticky;
  top: 72px;
  z-index: 4;
}

.toc-card {
  position: sticky;
  top: 210px;
  max-height: calc(100vh - 230px);
  overflow-y: auto;
}

.definition-card {
  scroll-margin-top: 225px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 12px;
  padding: 20px;
  overflow-wrap: anywhere;
}

.glossary-group {
  scroll-margin-top: 225px;
}

.glossary-card {
  cursor: pointer;
  overflow-wrap: anywhere;
}

code {
  white-space: normal;
  overflow-wrap: anywhere;
}

@media (max-width: 959px) {
  .search-card {
    position: static;
  }

  .definition-card {
    scroll-margin-top: 80px;
    padding: 16px;
  }

  .glossary-group {
    scroll-margin-top: 80px;
  }
}
</style>
