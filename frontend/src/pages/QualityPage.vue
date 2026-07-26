<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { qualityApi } from '../services/qualityApi'
import type { QualityReport, QualitySeverity } from '../types/quality'

const report = ref<QualityReport | null>(null)
const loading = ref(false)
const running = ref(false)
const error = ref<string | null>(null)
const severityFilter = ref<QualitySeverity | 'all'>('all')
const categoryFilter = ref('all')

const categories = computed(() => [...new Set(report.value?.issues.map((issue) => issue.category) ?? [])].sort())
const visibleIssues = computed(() => (report.value?.issues ?? []).filter((issue) => (
  (severityFilter.value === 'all' || issue.severity === severityFilter.value)
  && (categoryFilter.value === 'all' || issue.category === categoryFilter.value)
)))
const scoreColor = computed(() => {
  const score = report.value?.score ?? 0
  if (score >= 85) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
})

const severityLabels: Record<QualitySeverity, string> = {
  error: 'Fehler',
  warning: 'Warnung',
  info: 'Hinweis'
}
const severityColors: Record<QualitySeverity, string> = {
  error: 'error',
  warning: 'warning',
  info: 'info'
}
const categoryLabels: Record<string, string> = {
  assets: 'Assets',
  locations: 'Bereiche & Räume',
  electrical: 'Elektro',
  documents: 'Dokumente',
  knowledge: 'Wiki',
  maintenance: 'Wartung'
}

function severityLabel(value: QualitySeverity): string {
  return severityLabels[value]
}

function severityColor(value: QualitySeverity): string {
  return severityColors[value]
}

function categoryLabel(value: string): string {
  return categoryLabels[value] ?? value
}

async function load() {
  loading.value = true
  error.value = null
  try {
    report.value = await qualityApi.latest()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Qualitätsbericht konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

async function runCheck() {
  running.value = true
  error.value = null
  try {
    report.value = await qualityApi.run()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Qualitätsprüfung ist fehlgeschlagen.'
  } finally {
    running.value = false
  }
}

onMounted(() => void load())
</script>

<template>
  <v-container class="quality-page pa-4 pa-sm-6" fluid>
    <div class="d-flex flex-wrap align-center justify-space-between ga-3 mb-5">
      <div>
        <h1>Dokumentationsqualität</h1>
        <p class="text-medium-emphasis mb-0">Fehlende Angaben, defekte Verknüpfungen und überfällige Arbeiten erkennen.</p>
      </div>
      <v-btn color="primary" prepend-icon="mdi-refresh" :loading="running" @click="runCheck">
        Jetzt prüfen
      </v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4">{{ error }}</v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <template v-if="report">
      <v-row class="mb-3">
        <v-col cols="12" md="4">
          <v-card title="Qualitätswert" prepend-icon="mdi-clipboard-check-outline" height="100%">
            <v-card-text class="d-flex align-center ga-5">
              <v-progress-circular :model-value="report.score" :color="scoreColor" size="96" width="10">
                <strong>{{ report.score }}</strong>
              </v-progress-circular>
              <div>
                <div class="text-h6">von 100 Punkten</div>
                <div class="text-medium-emphasis">{{ report.issue_count }} Hinweise insgesamt</div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="4" md="2"><v-card title="Fehler"><v-card-text class="metric text-error">{{ report.error_count }}</v-card-text></v-card></v-col>
        <v-col cols="4" md="2"><v-card title="Warnungen"><v-card-text class="metric text-warning">{{ report.warning_count }}</v-card-text></v-card></v-col>
        <v-col cols="4" md="2"><v-card title="Hinweise"><v-card-text class="metric text-info">{{ report.info_count }}</v-card-text></v-card></v-col>
        <v-col cols="12" md="2">
          <v-card title="Letzte Prüfung" height="100%">
            <v-card-text>{{ new Date(report.completed_at).toLocaleString() }}</v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-card>
        <v-card-text class="d-flex flex-wrap ga-3">
          <v-select
            v-model="severityFilter"
            :items="[
              { title: 'Alle Schweregrade', value: 'all' },
              { title: 'Fehler', value: 'error' },
              { title: 'Warnungen', value: 'warning' },
              { title: 'Hinweise', value: 'info' }
            ]"
            label="Schweregrad"
            density="compact"
            hide-details
            max-width="240"
          />
          <v-select
            v-model="categoryFilter"
            :items="[
              { title: 'Alle Bereiche', value: 'all' },
              ...categories.map((category) => ({ title: categoryLabel(category), value: category }))
            ]"
            label="Bereich"
            density="compact"
            hide-details
            max-width="260"
          />
        </v-card-text>
        <v-list v-if="visibleIssues.length" lines="three">
          <v-list-item
            v-for="issue in visibleIssues"
            :key="issue.id"
            :prepend-icon="issue.severity === 'error' ? 'mdi-alert-outline' : 'mdi-information-outline'"
          >
            <v-list-item-title class="d-flex flex-wrap align-center ga-2">
              <span>{{ issue.title }}</span>
              <v-chip size="x-small" :color="severityColor(issue.severity)" variant="tonal">
                {{ severityLabel(issue.severity) }}
              </v-chip>
              <v-chip size="x-small" variant="outlined">{{ categoryLabel(issue.category) }}</v-chip>
            </v-list-item-title>
            <v-list-item-subtitle>{{ issue.description }}</v-list-item-subtitle>
            <template #append>
              <v-btn
                v-if="issue.route"
                :to="issue.route"
                icon="mdi-arrow-right"
                variant="text"
                aria-label="Betroffenen Eintrag öffnen"
              />
            </template>
          </v-list-item>
        </v-list>
        <v-card-text v-else class="text-medium-emphasis">
          Keine Hinweise für die gewählten Filter. Sehr gut.
        </v-card-text>
      </v-card>
    </template>
  </v-container>
</template>

<style scoped>
.quality-page {
  max-width: 1500px;
}
.metric {
  font-size: 2rem;
  font-weight: 700;
}
</style>
