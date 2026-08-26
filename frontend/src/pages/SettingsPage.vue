<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import ModuleSettingsCard from '../components/ModuleSettingsCard.vue'
import { immichApi } from '../services/immichApi'
import { validateIntegrationUrl } from '../services/integrationValidation'
import { settingsApi } from '../services/settingsApi'
import { useSettingsStore } from '../stores/settings'
import {
  createDefaultConfiguration,
  editableConfiguration,
  type IntegrationKind,
  type IntegrationTestResult,
  type McpSettingsWrite
} from '../types/settings'
import type { ImmichAlbum } from '../types/immich'

type FormHandle = { validate: () => Promise<{ valid: boolean }> }

const settings = useSettingsStore()
const formElement = ref<FormHandle | null>(null)
const form = ref(createDefaultConfiguration())
const loading = ref(true)
const saving = ref(false)
const testingKind = ref<IntegrationKind | null>(null)
const error = ref<string | null>(null)
const saved = ref(false)
const testResults = ref<Partial<Record<IntegrationKind, IntegrationTestResult>>>({})
const immichAlbums = ref<ImmichAlbum[]>([])
const immichAlbumsLoading = ref(false)
const immichAlbumsError = ref<string | null>(null)
const mcpForm = ref<McpSettingsWrite>({ enabled: false, permission: 'read', public_url: null })
const mcpTokenConfigured = ref(false)
const mcpToken = ref<string | null>(null)
const rotatingMcpToken = ref(false)
const copiedMcpToken = ref(false)
const copiedMcpUrl = ref(false)
const effectiveMcpUrl = computed(() => mcpForm.value.public_url?.trim() || `${window.location.origin}/mcp`)
const mcpUrlRule = (value: string | null) => {
  if (!value?.trim()) return true
  try {
    const parsed = new URL(value.trim())
    if (!['http:', 'https:'].includes(parsed.protocol)) return 'Bitte eine HTTP(S)-Adresse angeben.'
    if (parsed.username || parsed.password || parsed.search || parsed.hash) {
      return 'Die Adresse darf keine Zugangsdaten, Query-Parameter oder Fragmente enthalten.'
    }
    return parsed.pathname.replace(/\/+$/, '') === '/mcp' || 'Die Adresse muss auf /mcp enden.'
  } catch {
    return 'Bitte eine gültige MCP-Adresse angeben.'
  }
}

const integrationMeta: Record<IntegrationKind, {
  name: string
  icon: string
  secretLabel: string
  description: string
}> = {
  home_assistant: {
    name: 'Home Assistant',
    icon: 'mdi-home-assistant',
    secretLabel: 'Long-Lived Access Token',
    description: 'Prüft die REST-API und liest ausschließlich die Serverkonfiguration.'
  },
  immich: {
    name: 'Immich',
    icon: 'mdi-image-multiple',
    secretLabel: 'API-Key',
    description: 'Prüft den API-Key und liest die Immich-Serverversion.'
  },
  nextcloud: {
    name: 'Nextcloud',
    icon: 'mdi-cloud-outline',
    secretLabel: 'App-Passwort oder API-Token',
    description: 'Prüft die Anmeldung über eine schreibfreie WebDAV-Abfrage.'
  },
  fritzbox: {
    name: 'FRITZ!Box',
    icon: 'mdi-router-network',
    secretLabel: 'Kennwort',
    description: 'Liest Geräte ausschließlich über lokalen TR-064-Zugriff; es werden keine Einstellungen verändert.'
  }
}

const requiredRule = (value: string | null) => Boolean(value?.trim()) || 'Dieses Feld ist erforderlich.'
const secretRule = (kind: IntegrationKind, enabled: boolean, value: string | undefined) => {
  if (!enabled || value?.trim()) return true
  const stored = settings.configuration?.integrations.find((integration) => integration.kind === kind)
  return stored?.secret_configured || 'Bitte einen Schlüssel angeben.'
}

onMounted(async () => {
  try {
    const [configuration, mcpConfiguration] = await Promise.all([
      settings.fetchConfiguration(),
      settingsApi.readMcp()
    ])
    form.value = editableConfiguration(configuration)
    mcpForm.value = {
      enabled: mcpConfiguration.enabled,
      permission: mcpConfiguration.permission,
      public_url: mcpConfiguration.public_url
    }
    mcpTokenConfigured.value = mcpConfiguration.token_configured
    const immich = configuration.integrations.find((integration) => integration.kind === 'immich')
    if (immich?.enabled && immich.secret_configured) await loadImmichAlbums()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Einstellungen konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
})

async function loadImmichAlbums() {
  immichAlbumsLoading.value = true
  immichAlbumsError.value = null
  try {
    immichAlbums.value = (await immichApi.albums()).items
  } catch (reason) {
    immichAlbums.value = []
    immichAlbumsError.value = reason instanceof Error
      ? reason.message
      : 'Immich-Alben konnten nicht geladen werden.'
  } finally {
    immichAlbumsLoading.value = false
  }
}

function clearTestResult(kind: IntegrationKind) {
  delete testResults.value[kind]
  saved.value = false
}

async function persistConfiguration(): Promise<boolean> {
  const validation = await formElement.value?.validate()
  if (validation && !validation.valid) return false

  const configuration = await settings.saveConfiguration(form.value)
  form.value = editableConfiguration(configuration)
  return true
}

async function save() {
  saved.value = false
  error.value = null
  if (mcpForm.value.enabled && !mcpTokenConfigured.value) {
    error.value = 'Erzeuge zuerst einen MCP-Token, bevor du MCP aktivierst.'
    return
  }
  saving.value = true
  try {
    if (await persistConfiguration()) {
      const storedMcp = await settingsApi.updateMcp(mcpForm.value)
      mcpForm.value = {
        enabled: storedMcp.enabled,
        permission: storedMcp.permission,
        public_url: storedMcp.public_url
      }
      mcpTokenConfigured.value = storedMcp.token_configured
      saved.value = true
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Einstellungen konnten nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function rotateMcpToken() {
  rotatingMcpToken.value = true
  error.value = null
  saved.value = false
  try {
    const created = await settingsApi.rotateMcpToken()
    mcpToken.value = created.token
    mcpTokenConfigured.value = created.settings.token_configured
    copiedMcpToken.value = false
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'MCP-Token konnte nicht erzeugt werden.'
  } finally {
    rotatingMcpToken.value = false
  }
}

async function copyMcpToken() {
  if (!mcpToken.value) return
  try {
    await navigator.clipboard.writeText(mcpToken.value)
    copiedMcpToken.value = true
  } catch {
    error.value = 'Der MCP-Token konnte nicht in die Zwischenablage kopiert werden.'
  }
}

async function copyMcpUrl() {
  try {
    await navigator.clipboard.writeText(effectiveMcpUrl.value)
    copiedMcpUrl.value = true
  } catch {
    error.value = 'Die MCP-Adresse konnte nicht in die Zwischenablage kopiert werden.'
  }
}

async function testIntegration(kind: IntegrationKind) {
  testingKind.value = kind
  saved.value = false
  error.value = null
  delete testResults.value[kind]
  try {
    if (!await persistConfiguration()) return
    testResults.value[kind] = await settingsApi.testIntegration(kind)
    if (kind === 'immich' && testResults.value[kind]?.success) await loadImmichAlbums()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verbindungstest konnte nicht ausgeführt werden.'
  } finally {
    testingKind.value = null
  }
}
</script>

<template>
  <v-container class="settings-container pa-4 pa-sm-6" fluid>
    <div class="mb-6">
      <h1>Einstellungen</h1>
      <p class="text-medium-emphasis">
        Passe Darstellung, sichtbare Module und optionale Verbindungen deiner lokalen Installation an.
      </p>
    </div>

    <v-skeleton-loader v-if="loading" type="heading, paragraph, card, card" />

    <v-form v-else ref="formElement" @submit.prevent="save">
      <v-alert v-if="error" type="error" variant="tonal" class="mb-5" closable @click:close="error = null">
        {{ error }}
      </v-alert>
      <v-alert v-if="saved" type="success" variant="tonal" class="mb-5" closable>
        Einstellungen wurden gespeichert.
      </v-alert>

      <v-card title="Allgemein" prepend-icon="mdi-tune-variant" class="mb-5">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.installation_name"
                label="Name der Installation"
                :rules="[requiredRule]"
                maxlength="100"
                hint="Wird im Kopfbereich angezeigt und benennt den obersten Gebäudeeintrag."
                persistent-hint
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.timezone"
                label="IANA-Zeitzone"
                :rules="[requiredRule]"
                hint="Für Zeitstempel und spätere Zeitreihen, zum Beispiel Europe/Berlin."
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="form.language"
                label="Sprache"
                :items="[{ title: 'Deutsch', value: 'de' }, { title: 'English', value: 'en' }]"
                hint="Legt die bevorzugte Sprache für die Benutzeroberfläche fest."
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="form.theme"
                label="Design"
                :items="[{ title: 'Dark Mode', value: 'dark' }, { title: 'Light Mode', value: 'light' }]"
                hint="Ändert nur die Darstellung, nicht die gespeicherten Inhalte."
                persistent-hint
              />
            </v-col>
            <v-col cols="12">
              <v-switch
                v-model="form.online_product_image_search_enabled"
                color="primary"
                inset
                label="Online-Suche für Produktbilder erlauben"
                hint="Erlaubt die Suche ausschließlich über die unten aktivierten Quellen. Ein Treffer wird erst nach Auswahl lokal gespeichert."
                persistent-hint
              />
            </v-col>
            <v-col v-if="form.online_product_image_search_enabled" cols="12">
              <div class="text-subtitle-2 mb-1">Suchquellen</div>
              <div class="d-flex flex-wrap ga-4">
                <v-checkbox
                  v-model="form.product_image_source_duckduckgo_enabled"
                  label="DuckDuckGo Images"
                  hide-details
                />
                <v-checkbox
                  v-model="form.product_image_source_wikimedia_enabled"
                  label="Wikimedia Commons"
                  hide-details
                />
              </div>
              <v-alert
                v-if="!form.product_image_source_duckduckgo_enabled && !form.product_image_source_wikimedia_enabled"
                type="warning"
                density="compact"
                variant="tonal"
                class="mt-2"
              >
                Aktiviere mindestens eine Quelle, bevor du die Einstellungen speicherst.
              </v-alert>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <ModuleSettingsCard v-model="form.enabled_modules" class="mb-5" />

      <h2 class="text-h5 mb-1">Integrationen</h2>
      <p class="text-medium-emphasis mb-4">
        Alle Integrationen sind optional. Ein Verbindungstest speichert zuerst die aktuellen Eingaben
        und führt anschließend ausschließlich lesende Anfragen aus.
      </p>

      <v-card
        v-for="integration in form.integrations"
        :key="integration.kind"
        class="mb-4"
      >
        <v-card-title class="d-flex align-center ga-3">
          <v-icon :icon="integrationMeta[integration.kind].icon" color="primary" />
          {{ integrationMeta[integration.kind].name }}
          <v-spacer />
          <v-switch
            v-model="integration.enabled"
            color="primary"
            hide-details
            inset
            :aria-label="`${integrationMeta[integration.kind].name} aktivieren`"
            @update:model-value="clearTestResult(integration.kind)"
          />
        </v-card-title>
        <v-expand-transition>
          <v-card-text v-if="integration.enabled">
            <p class="text-medium-emphasis mb-4">
              {{ integrationMeta[integration.kind].description }}
            </p>
            <v-row>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="integration.base_url"
                  label="Server-URL"
                  prepend-inner-icon="mdi-web"
                  :rules="[(value) => validateIntegrationUrl(value, integration.enabled)]"
                  @update:model-value="clearTestResult(integration.kind)"
                />
              </v-col>
              <v-col v-if="integration.kind === 'nextcloud' || integration.kind === 'fritzbox'" cols="12" md="6">
                <v-text-field
                  v-model="integration.account"
                  label="Konto oder Benutzername"
                  prepend-inner-icon="mdi-account-outline"
                  maxlength="255"
                  :rules="[requiredRule]"
                  :hint="integration.kind === 'nextcloud' ? 'Für die WebDAV-Anmeldung erforderlich' : 'Eigener FRITZ!Box-Benutzer mit minimalen Rechten'"
                  persistent-hint
                  @update:model-value="clearTestResult(integration.kind)"
                />
              </v-col>
              <v-col v-if="integration.kind === 'nextcloud'" cols="12" md="6">
                <v-text-field
                  v-model="integration.document_root"
                  label="Dokumenten-Stammordner"
                  prepend-inner-icon="mdi-folder-outline"
                  maxlength="500"
                  :rules="[requiredRule]"
                  hint="Relativ zum Nextcloud-Benutzerordner, zum Beispiel DocOfHome/Documents"
                  persistent-hint
                  @update:model-value="clearTestResult(integration.kind)"
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-text-field
                  v-model="integration.secret"
                  :label="integrationMeta[integration.kind].secretLabel"
                  placeholder="Leer lassen, um den gespeicherten Wert beizubehalten"
                  type="password"
                  autocomplete="new-password"
                  prepend-inner-icon="mdi-key-outline"
                  :rules="[(value) => secretRule(integration.kind, integration.enabled, value)]"
                  persistent-placeholder
                  @update:model-value="clearTestResult(integration.kind)"
                />
              </v-col>
              <v-col v-if="integration.kind === 'immich'" cols="12">
                <div class="d-flex flex-column flex-sm-row align-sm-start ga-2">
                  <v-select
                    v-model="integration.selected_album_id"
                    label="Album für Asset- und Verteilungsbilder"
                    :items="immichAlbums"
                    item-title="album_name"
                    item-value="immich_album_id"
                    :loading="immichAlbumsLoading"
                    :disabled="immichAlbumsLoading"
                    clearable
                    persistent-hint
                    hint="Nur Bilder aus diesem Album werden bei Assets und Verteilungen angeboten."
                    @update:model-value="clearTestResult(integration.kind)"
                  >
                    <template #item="{ props, item }">
                      <v-list-item
                        v-bind="props"
                        :subtitle="`${item.raw.asset_count} Bilder`"
                      />
                    </template>
                  </v-select>
                  <v-btn
                    variant="tonal"
                    prepend-icon="mdi-refresh"
                    :loading="immichAlbumsLoading"
                    @click="loadImmichAlbums"
                  >
                    Alben laden
                  </v-btn>
                </div>
                <v-alert
                  v-if="immichAlbumsError"
                  type="warning"
                  variant="tonal"
                  density="compact"
                  class="mt-2"
                >
                  {{ immichAlbumsError }} Speichere oder prüfe zuerst die Immich-Verbindung.
                </v-alert>
              </v-col>
            </v-row>
            <v-alert type="info" variant="tonal" density="compact" icon="mdi-eye-off-outline" class="mb-4">
              Gespeicherte Secrets werden nicht angezeigt. Ein leerer Wert behält das vorhandene Secret bei.
            </v-alert>

            <v-alert
              v-if="testResults[integration.kind]"
              :type="testResults[integration.kind]?.success ? 'success' : 'error'"
              variant="tonal"
              class="mb-4"
            >
              <div class="font-weight-medium">{{ testResults[integration.kind]?.message }}</div>
              <div class="d-flex flex-wrap ga-2 mt-2">
                <v-chip
                  v-if="testResults[integration.kind]?.service_version"
                  size="small"
                  prepend-icon="mdi-information-outline"
                  variant="tonal"
                >
                  Version {{ testResults[integration.kind]?.service_version }}
                </v-chip>
                <v-chip size="small" prepend-icon="mdi-timer-outline" variant="tonal">
                  {{ testResults[integration.kind]?.response_time_ms }} ms
                </v-chip>
              </div>
            </v-alert>

            <div class="d-flex justify-end">
              <v-btn
                variant="tonal"
                color="primary"
                prepend-icon="mdi-connection"
                :loading="testingKind === integration.kind"
                :disabled="testingKind !== null && testingKind !== integration.kind"
                @click="testIntegration(integration.kind)"
              >
                Verbindung prüfen
              </v-btn>
            </div>
          </v-card-text>
        </v-expand-transition>
      </v-card>

      <v-card class="mt-6 mb-4">
        <v-card-title class="d-flex align-center ga-3">
          <v-icon icon="mdi-robot-outline" color="primary" />
          ChatGPT / MCP
          <v-spacer />
          <v-chip
            :color="mcpForm.enabled ? 'success' : 'default'"
            size="small"
            variant="tonal"
          >
            {{ mcpForm.enabled ? 'Aktiv' : 'Deaktiviert' }}
          </v-chip>
          <v-switch
            v-model="mcpForm.enabled"
            color="primary"
            hide-details
            inset
            aria-label="MCP-Zugriff aktivieren"
          />
        </v-card-title>
        <v-card-text>
          <p class="text-medium-emphasis mb-4">
            Stellt DocOfHome über den integrierten MCP-Endpunkt für ChatGPT und andere MCP-Clients bereit.
            Der Zugriff ist immer durch einen eigenen Bearer-Token geschützt.
          </p>

          <v-alert
            v-if="mcpForm.enabled && !mcpTokenConfigured"
            type="warning"
            variant="tonal"
            class="mb-4"
          >
            Erzeuge zuerst einen MCP-Token. Ohne Token lässt sich MCP nicht aktivieren.
          </v-alert>

          <v-row>
            <v-col cols="12" md="6">
              <v-select
                v-model="mcpForm.permission"
                label="Berechtigung"
                :items="[
                  { title: 'Nur lesen', value: 'read' },
                  { title: 'Lesen & Schreiben', value: 'write' },
                  { title: 'Vollzugriff', value: 'admin' }
                ]"
                hint="Schreiben erlaubt normale Einträge und Änderungen. Löschen ist nur mit Vollzugriff möglich."
                persistent-hint
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="mcpForm.public_url"
                label="Öffentliche MCP-Adresse"
                placeholder="https://mcp.example.de/mcp"
                prepend-inner-icon="mdi-web"
                :rules="[mcpUrlRule]"
                hint="Optional. Leer bedeutet die aktuelle DocOfHome-Adresse mit /mcp. Für SWAG kann hier der externe MCP-Hostname hinterlegt werden."
                persistent-hint
              />
            </v-col>
          </v-row>

          <v-alert type="info" variant="tonal" class="mt-2 mb-4">
            <div class="d-flex flex-column flex-sm-row align-sm-center ga-2">
              <div class="flex-grow-1">
                <div class="text-caption text-medium-emphasis">MCP-Verbindungsadresse</div>
                <code>{{ effectiveMcpUrl }}</code>
              </div>
              <v-btn
                variant="tonal"
                size="small"
                prepend-icon="mdi-content-copy"
                @click="copyMcpUrl"
              >
                {{ copiedMcpUrl ? 'Kopiert' : 'Adresse kopieren' }}
              </v-btn>
            </div>
          </v-alert>

          <div class="d-flex flex-column flex-md-row align-md-center ga-3 mb-3">
            <div class="flex-grow-1">
              <div class="text-subtitle-2">MCP-Token</div>
              <div class="text-medium-emphasis text-body-2">
                {{ mcpTokenConfigured ? 'Ein Token ist eingerichtet.' : 'Noch kein Token eingerichtet.' }}
                Gespeichert wird ausschließlich ein SHA-256-Hash.
              </div>
            </div>
            <v-btn
              color="primary"
              variant="tonal"
              prepend-icon="mdi-key-plus"
              :loading="rotatingMcpToken"
              @click="rotateMcpToken"
            >
              {{ mcpTokenConfigured ? 'Token erneuern' : 'Token erzeugen' }}
            </v-btn>
          </div>

          <v-alert v-if="mcpToken" type="warning" variant="tonal" class="mb-4">
            <div class="font-weight-medium mb-2">Neuen Token jetzt kopieren</div>
            <p class="mb-3">
              Aus Sicherheitsgründen wird der Token nur unmittelbar nach dem Erzeugen im Klartext angezeigt.
            </p>
            <v-text-field
              :model-value="mcpToken"
              label="MCP-Token"
              readonly
              hide-details
              class="mb-3"
            />
            <v-btn
              variant="tonal"
              prepend-icon="mdi-content-copy"
              @click="copyMcpToken"
            >
              {{ copiedMcpToken ? 'Token kopiert' : 'Token kopieren' }}
            </v-btn>
          </v-alert>

          <v-alert type="success" variant="tonal" density="compact" icon="mdi-shield-lock-outline">
            Empfohlen: Über den Reverse Proxy extern ausschließlich <code>/mcp</code> freigeben.
            Weboberfläche, REST-API und <code>/docs</code> müssen nicht öffentlich erreichbar sein.
          </v-alert>
        </v-card-text>
      </v-card>

      <div class="d-flex justify-end mt-6">
        <v-btn color="primary" size="large" type="submit" :loading="saving" prepend-icon="mdi-content-save">
          Einstellungen speichern
        </v-btn>
      </div>
    </v-form>
  </v-container>
</template>

<style scoped>
.settings-container { max-width: 1100px; }
h1 { font-size: clamp(1.8rem, 4vw, 2.25rem); }
</style>
