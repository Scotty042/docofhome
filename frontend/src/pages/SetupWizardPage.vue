<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'

import { validateIntegrationUrl } from '../services/integrationValidation'
import { settingsApi } from '../services/settingsApi'
import { locationApi } from '../services/locationApi'
import type { IntegrationTestResult } from '../types/settings'
import { useSettingsStore } from '../stores/settings'
import {
  createDefaultConfiguration,
  type IntegrationKind,
  type IntegrationWrite
} from '../types/settings'

type FormHandle = { validate: () => Promise<{ valid: boolean }> }

const router = useRouter()
const settings = useSettingsStore()
const theme = useTheme()
const formElement = ref<FormHandle | null>(null)
const currentStep = ref(1)
const configuration = ref(createDefaultConfiguration())
const submitting = ref(false)
const error = ref<string | null>(null)
const testingIntegration = ref(false)
const integrationTestResult = ref<IntegrationTestResult | null>(null)
const floorCount = ref(2)
const floors = ref([
  { name: 'Erdgeschoss', rooms: ['Wohnzimmer', 'Küche'] },
  { name: 'Obergeschoss', rooms: ['Schlafzimmer', 'Bad'] }
])
const hasOutdoor = ref(false)
const outdoorAreas = ref(['Garten'])

const steps = [
  'Willkommen',
  'Name der Installation',
  'Sprache',
  'Zeitzone',
  'Design',
  'Bereiche und Räume',
  'Home Assistant',
  'Immich',
  'Nextcloud',
  'FRITZ!Box',
  'Zusammenfassung',
  'Einrichtung abschließen'
]

const integrationStepKinds: Record<number, IntegrationKind> = {
  7: 'home_assistant',
  8: 'immich',
  9: 'nextcloud',
  10: 'fritzbox'
}

const integrationMeta: Record<IntegrationKind, {
  name: string
  icon: string
  description: string
  secretLabel: string
}> = {
  home_assistant: {
    name: 'Home Assistant',
    icon: 'mdi-home-assistant',
    description: 'Optional für eine spätere, ausschließlich lesende Smart-Home-Anbindung.',
    secretLabel: 'Long-Lived Access Token'
  },
  immich: {
    name: 'Immich',
    icon: 'mdi-image-multiple',
    description: 'Optional für spätere Bildverknüpfungen in deiner Dokumentation.',
    secretLabel: 'API-Key'
  },
  nextcloud: {
    name: 'Nextcloud',
    icon: 'mdi-cloud-outline',
    description: 'Optional für die spätere Ablage verwalteter Dokumente.',
    secretLabel: 'App-Passwort oder API-Token'
  },
  fritzbox: {
    name: 'FRITZ!Box',
    icon: 'mdi-router-wireless',
    description: 'Optional zum rein lesenden Import erkannter Netzwerkgeräte.',
    secretLabel: 'FRITZ!Box-Kennwort'
  }
}

const timezoneOptions = [
  configuration.value.timezone,
  'UTC',
  'Europe/Berlin',
  'Europe/Vienna',
  'Europe/Zurich',
  'Europe/London',
  'America/New_York',
  'America/Los_Angeles',
  'Asia/Tokyo',
  'Australia/Sydney'
].filter((value, index, values) => values.indexOf(value) === index)

const progress = computed(() => currentStep.value / 12 * 100)
const currentIntegration = computed<IntegrationWrite | null>(() => {
  const kind = integrationStepKinds[currentStep.value]
  if (!kind) return null
  return configuration.value.integrations.find((integration) => integration.kind === kind) ?? null
})
const currentIntegrationMeta = computed(() => {
  const integration = currentIntegration.value
  return integration ? integrationMeta[integration.kind] : null
})
const enabledIntegrations = computed(() => (
  configuration.value.integrations.filter((integration) => integration.enabled)
))

const requiredRule = (value: string | null) => Boolean(value?.trim()) || 'Dieses Feld ist erforderlich.'
const urlRule = (value: string | null) => validateIntegrationUrl(
  value,
  currentIntegration.value?.enabled ?? false
)
const secretRule = (value: string | undefined) => (
  !currentIntegration.value?.enabled || Boolean(value?.trim()) || 'Bitte einen Schlüssel angeben.'
)

async function nextStep() {
  error.value = null
  const validation = await formElement.value?.validate()
  if (validation && !validation.valid) return
  currentStep.value = Math.min(12, currentStep.value + 1)
}

function updateFloorCount(value: string | number | null) {
  const count = Math.max(1, Math.min(10, Number(value) || 1))
  floorCount.value = count
  while (floors.value.length < count) {
    floors.value.push({ name: `Etage ${floors.value.length + 1}`, rooms: [] })
  }
  floors.value.splice(count)
}

function previousStep() {
  error.value = null
  currentStep.value = Math.max(1, currentStep.value - 1)
}

function skipIntegration() {
  if (currentIntegration.value) {
    currentIntegration.value.enabled = false
    currentIntegration.value.base_url = null
    currentIntegration.value.account = null
    currentIntegration.value.secret = ''
    integrationTestResult.value = null
    currentIntegration.value.document_root = currentIntegration.value.kind === 'nextcloud'
      ? 'docofhome/Documents'
      : null
  }
  void nextStep()
}

function selectTheme(preference: 'dark' | 'light') {
  configuration.value.theme = preference
  theme.global.name.value = preference === 'light' ? 'jarvisLight' : 'jarvisDark'
}

async function testCurrentIntegration() {
  if (!currentIntegration.value) return
  error.value = null
  integrationTestResult.value = null
  const validation = await formElement.value?.validate()
  if (validation && !validation.valid) return
  testingIntegration.value = true
  try {
    integrationTestResult.value = await settingsApi.testIntegrationDraft(currentIntegration.value)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verbindungstest fehlgeschlagen.'
  } finally {
    testingIntegration.value = false
  }
}

async function createBuildingStructure() {
  const tree = await locationApi.tree()
  const building = tree.find((item) => item.location_type === 'building')
  if (!building) return
  for (let index = 0; index < floors.value.length; index += 1) {
    const floor = floors.value[index]
    if (!floor.name.trim()) continue
    const createdFloor = await locationApi.create({
      name: floor.name.trim(), location_type: 'floor', parent_id: building.id,
      description: null, short_name: null, sort_order: index, notes: null
    })
    for (let roomIndex = 0; roomIndex < floor.rooms.length; roomIndex += 1) {
      const name = floor.rooms[roomIndex]?.trim()
      if (!name) continue
      await locationApi.create({ name, location_type: 'room', parent_id: createdFloor.id,
        description: null, short_name: null, sort_order: roomIndex, notes: null })
    }
  }
  if (hasOutdoor.value) {
    for (let index = 0; index < outdoorAreas.value.length; index += 1) {
      const name = outdoorAreas.value[index]?.trim()
      if (!name) continue
      await locationApi.create({ name, location_type: 'outdoor', parent_id: building.id,
        description: null, short_name: null, sort_order: index, notes: null })
    }
  }
}

async function completeSetup() {
  submitting.value = true
  error.value = null
  try {
    await settings.completeSetup(configuration.value)
    await createBuildingStructure()
    await router.replace({ name: 'dashboard' })
  } catch (reason) {
    error.value = reason instanceof Error
      ? reason.message
      : 'Die Einrichtung konnte nicht gespeichert werden. Bitte versuche es erneut.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="wizard-shell">
    <v-container class="wizard-container" fluid>
      <div class="wizard-brand mb-6">
        <v-icon icon="mdi-home-lightning-bolt-outline" size="34" color="primary" />
        <div>
          <strong>DocOfHome</strong>
          <span>Know your home.</span>
        </div>
      </div>

      <v-card class="wizard-card" rounded="xl" elevation="12">
        <div class="wizard-progress pa-5 pb-2">
          <div class="d-flex justify-space-between align-center mb-2">
            <span class="text-caption text-medium-emphasis">Schritt {{ currentStep }} von 12</span>
            <span class="text-caption font-weight-medium">{{ steps[currentStep - 1] }}</span>
          </div>
          <v-progress-linear :model-value="progress" color="primary" height="6" rounded />
        </div>

        <v-form ref="formElement" class="wizard-content" @submit.prevent>
          <v-window v-model="currentStep">
            <v-window-item :value="1">
              <section class="step centered-step">
                <v-avatar color="primary" variant="tonal" size="88" class="mb-6">
                  <v-icon icon="mdi-creation-outline" size="46" />
                </v-avatar>
                <h1>Willkommen bei DocOfHome</h1>
                <p class="step-lead">
                  In wenigen Schritten richtest du deinen digitalen Zwilling ein. Alle Angaben
                  bleiben in deiner persistenten lokalen SQLite-Datenbank.
                </p>
                <v-alert type="info" variant="tonal" class="mt-5 text-left" icon="mdi-shield-lock-outline">
                  Integrationen sind optional. DocOfHome funktioniert vollständig ohne externe Dienste.
                </v-alert>
              </section>
            </v-window-item>

            <v-window-item :value="2">
              <section class="step">
                <v-icon icon="mdi-home-edit-outline" size="42" color="primary" class="mb-4" />
                <h1>Wie soll deine Installation heißen?</h1>
                <p class="step-lead">Dieser Name erscheint später in der Navigation und im Dashboard.</p>
                <v-text-field
                  v-model="configuration.installation_name"
                  label="Name der Installation"
                  placeholder="z. B. Zuhause"
                  prepend-inner-icon="mdi-home-outline"
                  :rules="[requiredRule]"
                  maxlength="100"
                  counter
                  autofocus
                />
              </section>
            </v-window-item>

            <v-window-item :value="3">
              <section class="step">
                <v-icon icon="mdi-translate" size="42" color="primary" class="mb-4" />
                <h1>Sprache auswählen</h1>
                <p class="step-lead">Du kannst diese Einstellung später jederzeit ändern.</p>
                <v-radio-group v-model="configuration.language" class="choice-group">
                  <v-radio label="Deutsch" value="de" color="primary" />
                  <v-radio label="English" value="en" color="primary" />
                </v-radio-group>
              </section>
            </v-window-item>

            <v-window-item :value="4">
              <section class="step">
                <v-icon icon="mdi-map-clock-outline" size="42" color="primary" class="mb-4" />
                <h1>Zeitzone festlegen</h1>
                <p class="step-lead">Zeitangaben für Wartung und Verlauf werden damit korrekt dargestellt.</p>
                <v-combobox
                  v-model="configuration.timezone"
                  :items="timezoneOptions"
                  label="IANA-Zeitzone"
                  prepend-inner-icon="mdi-clock-outline"
                  :rules="[requiredRule]"
                  hint="Beispiel: Europe/Berlin"
                  persistent-hint
                />
              </section>
            </v-window-item>

            <v-window-item :value="5">
              <section class="step">
                <v-icon icon="mdi-theme-light-dark" size="42" color="primary" class="mb-4" />
                <h1>Design auswählen</h1>
                <p class="step-lead">Dark Mode ist standardmäßig ausgewählt.</p>
                <v-row>
                  <v-col cols="12" sm="6">
                    <v-card
                      class="theme-choice"
                      :class="{ selected: configuration.theme === 'dark' }"
                      variant="outlined"
                      tabindex="0"
                      @click="selectTheme('dark')"
                      @keydown.enter="selectTheme('dark')"
                    >
                      <v-card-text>
                        <v-icon icon="mdi-weather-night" size="34" class="mb-3" />
                        <h2>Dark Mode</h2>
                        <p class="text-medium-emphasis">Ruhig, kontrastreich und vorausgewählt.</p>
                      </v-card-text>
                    </v-card>
                  </v-col>
                  <v-col cols="12" sm="6">
                    <v-card
                      class="theme-choice"
                      :class="{ selected: configuration.theme === 'light' }"
                      variant="outlined"
                      tabindex="0"
                      @click="selectTheme('light')"
                      @keydown.enter="selectTheme('light')"
                    >
                      <v-card-text>
                        <v-icon icon="mdi-white-balance-sunny" size="34" class="mb-3" />
                        <h2>Light Mode</h2>
                        <p class="text-medium-emphasis">Hell und klar für lichtreiche Umgebungen.</p>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>
              </section>
            </v-window-item>

            <v-window-item :value="6">
              <section class="step">
                <v-icon icon="mdi-home-group" size="42" color="primary" class="mb-4" />
                <h1>Etagen und Räume anlegen</h1>
                <p class="step-lead">DocOfHome legt die Gebäudestruktur beim Abschluss automatisch an.</p>
                <v-text-field v-model.number="floorCount" type="number" label="Wie viele Etagen gibt es?"
                  :min="1" :max="10" @update:model-value="updateFloorCount" />
                <v-card v-for="(floor, floorIndex) in floors" :key="floorIndex" variant="outlined" class="mb-3">
                  <v-card-text>
                    <v-text-field v-model="floor.name" :label="`Name der Etage ${floorIndex + 1}`" />
                    <v-combobox v-model="floor.rooms" label="Räume auf dieser Etage" multiple chips closable-chips
                      hint="Raumnamen eingeben und jeweils mit Enter bestätigen" persistent-hint />
                  </v-card-text>
                </v-card>
                <v-switch v-model="hasOutdoor" label="Es gibt einen Außenbereich" color="primary" inset />
                <v-combobox v-if="hasOutdoor" v-model="outdoorAreas" label="Außenbereiche" multiple chips closable-chips
                  hint="Zum Beispiel Garten, Terrasse, Hof oder Garage" persistent-hint />
              </section>
            </v-window-item>

            <v-window-item v-for="stepNumber in [7, 8, 9, 10]" :key="stepNumber" :value="stepNumber">
              <section v-if="currentIntegration && currentIntegrationMeta" class="step">
                <v-icon :icon="currentIntegrationMeta.icon" size="42" color="primary" class="mb-4" />
                <h1>{{ currentIntegrationMeta.name }}</h1>
                <p class="step-lead">{{ currentIntegrationMeta.description }}</p>
                <v-switch
                  v-model="currentIntegration.enabled"
                  label="Integration aktivieren"
                  color="primary"
                  inset
                  hide-details
                  class="mb-5"
                />
                <div v-if="currentIntegration.enabled">
                  <v-text-field
                    v-model="currentIntegration.base_url"
                    label="Server-URL"
                    placeholder="https://dienst.example.test"
                    prepend-inner-icon="mdi-web"
                    :rules="[urlRule]"
                    class="mb-2"
                  />
                  <v-text-field
                    v-model="currentIntegration.secret"
                    :label="currentIntegrationMeta.secretLabel"
                    type="password"
                    autocomplete="new-password"
                    prepend-inner-icon="mdi-key-outline"
                    :rules="[secretRule]"
                  />
                  <v-text-field
                    v-if="currentIntegration.kind === 'nextcloud' || currentIntegration.kind === 'fritzbox'"
                    v-model="currentIntegration.account"
                    label="Konto oder Benutzername"
                    prepend-inner-icon="mdi-account-outline"
                    maxlength="255"
                    :rules="[requiredRule]"
                    hint="Separat von App-Passwort oder Token gespeichert"
                    persistent-hint
                    class="mb-2"
                  />
                  <v-text-field
                    v-if="currentIntegration.kind === 'nextcloud'"
                    v-model="currentIntegration.document_root"
                    label="Dokumenten-Stammordner"
                    prepend-inner-icon="mdi-folder-outline"
                    maxlength="500"
                    :rules="[requiredRule]"
                    hint="Relativ zum Benutzerordner, zum Beispiel DocOfHome/Documents"
                    persistent-hint
                    class="mb-4"
                  />
                  <v-alert
                    v-if="currentIntegration.kind === 'immich'"
                    type="info" variant="tonal" density="compact" icon="mdi-shield-key-outline" class="mb-3"
                  >
                    Der Immich-API-Key benötigt Leserechte für API-Key-Informationen, Server-Version,
                    Alben, Assets und Vorschaubilder. DocOfHome verändert oder löscht keine Inhalte in Immich.
                  </v-alert>
                  <v-alert type="info" variant="tonal" density="compact" icon="mdi-eye-off-outline" class="mb-3">
                    Der Schlüssel wird gespeichert, aber niemals vollständig an den Browser zurückgegeben.
                  </v-alert>
                  <v-alert
                    v-if="integrationTestResult"
                    :type="integrationTestResult.success ? 'success' : 'error'"
                    variant="tonal" density="compact" class="mb-3"
                  >
                    {{ integrationTestResult.message }} ({{ integrationTestResult.response_time_ms }} ms)
                  </v-alert>
                  <div class="d-flex justify-end">
                    <v-btn variant="tonal" color="primary" prepend-icon="mdi-connection"
                      :loading="testingIntegration" @click="testCurrentIntegration">
                      Verbindung prüfen
                    </v-btn>
                  </div>
                </div>
                <v-alert v-else type="success" variant="tonal" icon="mdi-check-circle-outline">
                  Überspringen ist völlig in Ordnung. Die Integration kann später aktiviert werden.
                </v-alert>
              </section>
            </v-window-item>

            <v-window-item :value="11">
              <section class="step">
                <v-icon icon="mdi-clipboard-check-outline" size="42" color="primary" class="mb-4" />
                <h1>Zusammenfassung</h1>
                <p class="step-lead">Prüfe deine Auswahl. Noch wurde nichts gespeichert.</p>
                <v-list bg-color="transparent" lines="two">
                  <v-list-item prepend-icon="mdi-home-outline" title="Installation" :subtitle="configuration.installation_name" />
                  <v-list-item prepend-icon="mdi-translate" title="Sprache" :subtitle="configuration.language === 'de' ? 'Deutsch' : 'English'" />
                  <v-list-item prepend-icon="mdi-clock-outline" title="Zeitzone" :subtitle="configuration.timezone" />
                  <v-list-item prepend-icon="mdi-theme-light-dark" title="Design" :subtitle="configuration.theme === 'dark' ? 'Dark Mode' : 'Light Mode'" />
                </v-list>
                <v-divider class="my-3" />
                <h2 class="text-subtitle-1 mb-2">Integrationen</h2>
                <v-chip
                  v-for="integration in configuration.integrations"
                  :key="integration.kind"
                  class="mr-2 mb-2"
                  :color="integration.enabled ? 'success' : undefined"
                  :prepend-icon="integration.enabled ? 'mdi-check' : 'mdi-minus'"
                  variant="tonal"
                >
                  {{ integrationMeta[integration.kind].name }}:
                  {{ integration.enabled ? 'aktiv' : 'übersprungen' }}
                </v-chip>
              </section>
            </v-window-item>

            <v-window-item :value="12">
              <section class="step centered-step">
                <v-avatar color="success" variant="tonal" size="88" class="mb-6">
                  <v-icon icon="mdi-check-bold" size="44" />
                </v-avatar>
                <h1>Bereit für DocOfHome</h1>
                <p class="step-lead">
                  Mit „Einrichtung abschließen“ wird die gesamte Konfiguration in einer Transaktion
                  gespeichert. Danach öffnet sich dein Dashboard.
                </p>
                <p class="text-medium-emphasis">
                  {{ enabledIntegrations.length }} von 4 optionalen Integrationen aktiviert
                </p>
              </section>
            </v-window-item>
          </v-window>
        </v-form>

        <v-alert v-if="error" type="error" variant="tonal" class="mx-5 mb-2">
          {{ error }}
        </v-alert>

        <v-card-actions class="wizard-actions pa-5 pt-3">
          <v-btn v-if="currentStep > 1" variant="text" prepend-icon="mdi-arrow-left" @click="previousStep">
            Zurück
          </v-btn>
          <v-spacer />
          <v-btn
            v-if="currentStep >= 7 && currentStep <= 10"
            variant="text"
            class="mr-2"
            @click="skipIntegration"
          >
            Überspringen
          </v-btn>
          <v-btn
            v-if="currentStep < 12"
            color="primary"
            variant="flat"
            append-icon="mdi-arrow-right"
            @click="nextStep"
          >
            Weiter
          </v-btn>
          <v-btn
            v-else
            color="success"
            variant="flat"
            prepend-icon="mdi-check"
            :loading="submitting"
            @click="completeSetup"
          >
            Einrichtung abschließen
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-container>
  </div>
</template>

<style scoped>
.wizard-shell {
  min-height: 100vh;
  background:
    radial-gradient(circle at 15% 20%, rgba(var(--v-theme-primary), 0.16), transparent 35%),
    rgb(var(--v-theme-background));
}

.wizard-container {
  max-width: 920px;
  padding: clamp(1rem, 4vw, 3rem);
}

.wizard-brand {
  display: flex;
  gap: 0.8rem;
  align-items: center;
}

.wizard-brand strong,
.wizard-brand span {
  display: block;
}

.wizard-brand strong { font-size: 1.2rem; letter-spacing: 0.08em; }
.wizard-brand span { color: rgb(var(--v-theme-secondary)); font-size: 0.85rem; }
.wizard-card { overflow: hidden; }
.wizard-content { min-height: 470px; }
.step { max-width: 680px; margin: 0 auto; padding: clamp(2rem, 6vw, 4.5rem) clamp(1.25rem, 6vw, 4rem); }
.centered-step { text-align: center; }
.step h1 { margin-bottom: 0.75rem; font-size: clamp(1.65rem, 4vw, 2.25rem); line-height: 1.15; }
.step-lead { margin-bottom: 2rem; color: rgb(var(--v-theme-secondary)); font-size: 1.05rem; }
.choice-group { max-width: 420px; }
.theme-choice { height: 100%; cursor: pointer; transition: border-color 150ms, background 150ms; }
.theme-choice.selected { border-color: rgb(var(--v-theme-primary)); background: rgba(var(--v-theme-primary), 0.08); }

@media (max-width: 600px) {
  .wizard-container { padding: 0; }
  .wizard-brand { padding: 1rem 1.25rem 0; }
  .wizard-card { min-height: calc(100vh - 70px); border-radius: 24px 24px 0 0 !important; }
  .wizard-content { min-height: 520px; }
  .wizard-actions { position: sticky; bottom: 0; background: rgb(var(--v-theme-surface)); }
  .wizard-actions .v-btn { padding-inline: 0.65rem; }
}
</style>
