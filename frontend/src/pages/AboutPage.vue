<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import SafeMarkdown from '../components/SafeMarkdown.vue'
import { aboutApi } from '../services/aboutApi'
import { useNotificationStore } from '../stores/notifications'
import type {
  AboutInformation,
  FeedbackCategory,
  FeedbackTechnicalInfo,
  FeedbackWrite
} from '../types/about'

type FormHandle = { validate: () => Promise<{ valid: boolean }> }

const route = useRoute()
const notifications = useNotificationStore()
const loading = ref(true)
const sending = ref(false)
const error = ref<string | null>(null)
const information = ref<AboutInformation | null>(null)
const tab = ref('project')
const openReleases = ref<string[]>([])
const feedbackForm = ref<FormHandle | null>(null)
const feedback = ref<FeedbackWrite>(emptyFeedback())

const categoryItems: Array<{ title: string; value: FeedbackCategory }> = [
  { title: 'Fehler', value: 'error' },
  { title: 'Verbesserung', value: 'improvement' },
  { title: 'Bedienung', value: 'usability' },
  { title: 'Dokumentation', value: 'documentation' },
  { title: 'Sonstiges', value: 'other' }
]

const tabs = computed(() => [
  { value: 'project', title: 'Projekt', icon: 'mdi-home-heart' },
  { value: 'versions', title: 'Versionen & Changelog', icon: 'mdi-history' },
  { value: 'feedback', title: 'Feedback', icon: 'mdi-message-text-outline' }
])

const technicalInfo = computed<FeedbackTechnicalInfo>(() => ({
  app_version: information.value?.version ?? null,
  route: feedback.value.current_page,
  user_agent: navigator.userAgent,
  viewport: `${window.innerWidth} × ${window.innerHeight}`
}))

function emptyFeedback(): FeedbackWrite {
  const from = typeof route.query.from === 'string' ? route.query.from : null
  return {
    category: 'improvement',
    subject: '',
    description: '',
    current_page: from,
    include_technical_info: false,
    technical_info: null
  }
}

function formatDate(value: string | null) {
  if (!value) return 'Datum nicht angegeben'
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'long' }).format(
    new Date(`${value}T00:00:00`)
  )
}

async function sendFeedback() {
  const validation = await feedbackForm.value?.validate()
  if (validation && !validation.valid) return
  sending.value = true
  error.value = null
  try {
    const result = await aboutApi.sendFeedback({
      ...feedback.value,
      current_page: feedback.value.current_page?.trim() || null,
      technical_info: feedback.value.include_technical_info ? technicalInfo.value : null
    })
    notifications.success(`${result.message} Referenz: ${result.reference}`)
    feedback.value = emptyFeedback()
  } catch (reason) {
    const message = reason instanceof Error ? reason.message : 'Feedback konnte nicht gesendet werden.'
    error.value = message
    notifications.error(message)
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  try {
    information.value = await aboutApi.read()
    const current = information.value.releases.find((item) => item.current)
    if (current) openReleases.value = [current.version]
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Informationen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <v-container class="about-container pa-4 pa-md-6" fluid>
    <div class="d-flex flex-wrap align-center ga-3 mb-6">
      <div>
        <h1 class="text-h4 font-weight-bold">Über DocOfHome</h1>
        <p class="text-medium-emphasis">Projektinformationen, Versionen und Angaben zu dieser Installation.</p>
      </div>
      <v-spacer />
      <v-chip v-if="information" color="primary" size="large" prepend-icon="mdi-tag-outline">
        Version {{ information.version }}
      </v-chip>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" closable class="mb-5" @click:close="error = null">
      {{ error }}
    </v-alert>
    <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />

    <template v-else-if="information">
      <v-tabs v-model="tab" show-arrows class="mb-5">
        <v-tab v-for="item in tabs" :key="item.value" :value="item.value" :prepend-icon="item.icon">
          {{ item.title }}
        </v-tab>
      </v-tabs>

      <v-window v-model="tab">
        <v-window-item value="project">
          <v-row>
            <v-col cols="12" md="7">
              <v-card title="DocOfHome" prepend-icon="mdi-home-heart" height="100%">
                <v-card-text>
                  <p class="text-body-1 mb-4">{{ information.project_summary }}</p>
                  <v-alert type="info" variant="tonal" icon="mdi-shield-home-outline" class="mb-4">
                    {{ information.data_sovereignty }}
                  </v-alert>
                  <p v-if="information.license_notice" class="text-medium-emphasis mb-0">
                    {{ information.license_notice }}
                  </p>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" md="5">
              <v-card title="Projektverweise" prepend-icon="mdi-open-in-new" height="100%">
                <v-list v-if="information.links.length" lines="two">
                  <v-list-item
                    v-for="link in information.links"
                    :key="link.url"
                    :href="link.url"
                    target="_blank"
                    rel="noopener noreferrer"
                    :prepend-icon="link.icon"
                    :title="link.label"
                    subtitle="Öffnet in einem neuen Tab"
                    append-icon="mdi-open-in-new"
                  />
                </v-list>
                <v-card-text v-else class="text-medium-emphasis">
                  Im Paket sind derzeit keine externen Projektverweise hinterlegt.
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </v-window-item>

        <v-window-item value="versions">
          <v-card title="Versionen & Changelog" prepend-icon="mdi-history">
            <v-card-text class="pb-0">
              Die Inhalte werden direkt aus den mit dem Release ausgelieferten Release Notes gelesen.
            </v-card-text>
            <v-expansion-panels v-model="openReleases" multiple variant="accordion" class="pa-4">
              <v-expansion-panel
                v-for="release in information.releases"
                :key="release.version"
                :value="release.version"
              >
                <v-expansion-panel-title>
                  <div class="d-flex flex-wrap align-center ga-2">
                    <strong>Version {{ release.version }}</strong>
                    <v-chip v-if="release.current" color="primary" size="small">Installiert</v-chip>
                    <span class="text-caption text-medium-emphasis">{{ formatDate(release.release_date) }}</span>
                  </div>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <SafeMarkdown :source="release.markdown" />
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card>
        </v-window-item>

        <v-window-item value="feedback">
          <v-card title="Feedback senden" prepend-icon="mdi-message-text-outline" max-width="900">
            <v-card-text>
              <v-alert
                v-if="!information.feedback_available"
                type="warning"
                variant="tonal"
                class="mb-5"
              >
                {{ information.feedback_unavailable_reason }}
              </v-alert>
              <v-alert type="info" variant="tonal" density="compact" class="mb-5">
                Das Feedback wird als kleines ZIP an den öffentlichen DocOfHome-File-Drop übertragen.
                Es enthält nur deine Eingaben und optional ausdrücklich freigegebene technische Angaben.
              </v-alert>
              <v-form ref="feedbackForm" @submit.prevent="sendFeedback">
                <v-row>
                  <v-col cols="12" sm="5">
                    <v-select v-model="feedback.category" :items="categoryItems" label="Kategorie" />
                  </v-col>
                  <v-col cols="12" sm="7">
                    <v-text-field
                      v-model="feedback.subject"
                      label="Betreff"
                      maxlength="150"
                      counter
                      :rules="[(value) => (value?.trim().length >= 3) || 'Mindestens 3 Zeichen angeben.']"
                    />
                  </v-col>
                  <v-col cols="12">
                    <v-textarea
                      v-model="feedback.description"
                      label="Beschreibung"
                      rows="7"
                      maxlength="10000"
                      counter
                      :rules="[(value) => (value?.trim().length >= 10) || 'Bitte das Anliegen etwas genauer beschreiben.']"
                    />
                  </v-col>
                  <v-col cols="12">
                    <v-text-field
                      v-model="feedback.current_page"
                      label="Betroffene Seite (optional)"
                      placeholder="Zum Beispiel /electrical oder /consumption"
                      maxlength="500"
                      clearable
                    />
                  </v-col>
                  <v-col cols="12">
                    <v-switch
                      v-model="feedback.include_technical_info"
                      color="primary"
                      inset
                      label="Die unten aufgeführten technischen Informationen mitsenden"
                    />
                    <v-expand-transition>
                      <v-alert v-if="feedback.include_technical_info" type="info" variant="tonal" density="compact">
                        <div>Übertragen werden ausschließlich:</div>
                        <ul class="pl-5 mt-1">
                          <li>DocOfHome-Version: {{ technicalInfo.app_version }}</li>
                          <li>Route: {{ technicalInfo.route || 'nicht angegeben' }}</li>
                          <li>Browserkennung: {{ technicalInfo.user_agent }}</li>
                          <li>Fenstergröße: {{ technicalInfo.viewport }}</li>
                        </ul>
                        Tokens, Passwörter und Konfigurationen werden nicht übertragen.
                      </v-alert>
                    </v-expand-transition>
                  </v-col>
                </v-row>
                <div class="d-flex justify-end mt-4">
                  <v-btn
                    type="submit"
                    color="primary"
                    size="large"
                    prepend-icon="mdi-send"
                    :loading="sending"
                    :disabled="sending || !information.feedback_available"
                  >
                    Feedback senden
                  </v-btn>
                </div>
              </v-form>
            </v-card-text>
          </v-card>
        </v-window-item>

      </v-window>
    </template>
  </v-container>
</template>

<style scoped>
.about-container {
  max-width: 1200px;
}

.preserve-lines {
  white-space: pre-line;
}
</style>
