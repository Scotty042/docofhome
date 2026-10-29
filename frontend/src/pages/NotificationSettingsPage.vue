<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { notificationApi } from '../services/notificationApi'
import { useSettingsStore } from '../stores/settings'
import { defaultPushConfig, editablePushConfig } from '../types/notifications'
import type { PushDelivery, PushProvider, PushRead } from '../types/notifications'

const settings = useSettingsStore()
const form = ref(defaultPushConfig())
const stored = ref<PushRead | null>(null)
const baseline = ref('')
const loading = ref(true)
const saving = ref(false)
const testing = ref<PushProvider | null>(null)
const history = ref<PushDelivery[]>([])
const error = ref('')
const result = ref<{ success: boolean, message: string } | null>(null)
const dirty = computed(() => !loading.value && JSON.stringify(form.value) !== baseline.value)
const busy = computed(() => saving.value || testing.value !== null)
const sendTime = computed({
  get: () => `${String(form.value.send_hour).padStart(2, '0')}:${String(form.value.send_minute).padStart(2, '0')}`,
  set: (value: string) => { if (/^\d{2}:\d{2}$/.test(value)) { const [h, m] = value.split(':').map(Number); form.value.send_hour = h!; form.value.send_minute = m! } }
})
function accept(data: PushRead) {
  stored.value = data
  form.value = editablePushConfig(data)
  baseline.value = JSON.stringify(form.value)
}
async function refreshHistory() { history.value = await notificationApi.history() }
onMounted(async () => {
  try { accept(await notificationApi.read()); await refreshHistory() }
  catch (e) { error.value = e instanceof Error ? e.message : 'Einstellungen konnten nicht geladen werden' }
  finally { loading.value = false }
})
function payload() {
  const data = { ...form.value, public_url: form.value.public_url?.trim() || null }
  for (const key of ['pushover_app_token', 'pushover_user_key', 'ntfy_access_token'] as const) {
    if (data[`clear_${key}`]) delete data[key]
  }
  return data
}
async function save() {
  if (busy.value || !stored.value) return
  saving.value = true; error.value = ''; result.value = null
  try { accept(await notificationApi.save(payload())); result.value = { success: true, message: 'Benachrichtigungen gespeichert' } }
  catch (e) { error.value = e instanceof Error ? e.message : 'Speichern fehlgeschlagen' }
  finally { saving.value = false }
}
function discard() {
  if (busy.value || !stored.value) return
  if (dirty.value && !window.confirm('Ungespeicherte Push-Einstellungen verwerfen?')) return
  accept(stored.value); result.value = null; error.value = ''
}
async function test(provider: PushProvider) {
  if (busy.value || !stored.value) return
  testing.value = provider; error.value = ''; result.value = null
  try { result.value = await notificationApi.test(provider, payload()); await refreshHistory() }
  catch (e) { error.value = e instanceof Error ? e.message : 'Test fehlgeschlagen' }
  finally { testing.value = null }
}
function beforeUnload(event: BeforeUnloadEvent) { if (dirty.value) { event.preventDefault(); event.returnValue = '' } }
window.addEventListener('beforeunload', beforeUnload)
onBeforeUnmount(() => window.removeEventListener('beforeunload', beforeUnload))
onBeforeRouteLeave(() => !busy.value && (!dirty.value || window.confirm('Ungespeicherte Push-Einstellungen verwerfen und die Seite verlassen?')))
const timestamp = (value: string | null) => value ? new Date(value.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`).toLocaleString('de-DE') : '–'
const statusName = (value: string) => ({ sent: 'Angenommen', failed: 'Fehlgeschlagen', sending: 'Versand läuft', pending: 'Ausstehend' })[value] || value
</script>

<template>
  <v-container class="push-settings py-6" fluid>
    <div class="d-flex flex-wrap align-center ga-3 mb-5"><div><h1>Push-Benachrichtigungen</h1><p class="text-medium-emphasis">Einstellungen · Erinnerungen auf dein Smartphone</p></div><v-spacer /><v-btn to="/wiki/handbuch" variant="text" prepend-icon="mdi-book-open-page-variant">Handbuch</v-btn><v-btn to="/settings" variant="text">Zurück zu Einstellungen</v-btn></div>
    <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>
    <v-alert v-if="result" :type="result.success ? 'success' : 'error'" class="mb-4">{{ result.message }}</v-alert>
    <v-skeleton-loader v-if="loading" type="card, card" />
    <v-form v-else @submit.prevent="save">
      <fieldset :disabled="busy || !stored" class="push-fields">
      <v-card class="mb-5" title="Erinnerungen und Versand" prepend-icon="mdi-bell-outline"><v-card-text>
        <v-switch v-model="form.enabled" color="primary" label="Automatische Push-Erinnerungen aktivieren" inset />
        <div class="d-flex flex-wrap ga-4"><v-checkbox v-model="form.readings_enabled" label="Zähler ablesen" /><v-checkbox v-model="form.maintenance_enabled" label="Wartungsarbeiten" /><v-checkbox v-model="form.tasks_enabled" label="Aufgaben und Termine" /></div>
        <v-row><v-col cols="12" sm="6"><v-text-field v-model="sendTime" type="time" label="Tägliche Versandzeit" :hint="`Zeitzone der Installation: ${settings.configuration?.timezone || 'Europe/Berlin'}`" persistent-hint /></v-col><v-col cols="12" sm="6"><v-text-field v-model.number="form.days_ahead" type="number" min="0" max="31" step="1" label="Vorlauf in Tagen" hint="0 = heute und überfällig; maximal 31 Tage" persistent-hint /></v-col></v-row>
        <v-text-field v-model="form.public_url" label="Öffentliche DocOfHome-Adresse (optional)" placeholder="https://zuhause.example.de" hint="Ohne Unterpfad. Fügt der Nachricht einen Link zur passenden Übersicht hinzu." persistent-hint class="mt-4" clearable />
        <p class="text-medium-emphasis mt-4">Eine tägliche Zusammenfassung pro aktiviertem Dienst. Offene überfällige Einträge bleiben enthalten, bis sie erledigt sind. Ohne offene Erinnerungen erfolgt kein Versand.</p>
      </v-card-text></v-card>
      <v-row><v-col cols="12" lg="6"><v-card height="100%" title="Pushover" prepend-icon="mdi-cellphone-message"><v-card-text>
        <v-switch v-model="form.pushover_enabled" label="Pushover verwenden" color="primary" inset />
        <v-text-field v-model="form.pushover_app_token" type="password" autocomplete="new-password" label="Application API Token" :placeholder="stored?.pushover_app_token_configured ? 'Gespeichert – leer lassen zum Beibehalten' : 'App-Token eingeben'" :disabled="form.clear_pushover_app_token" />
        <v-checkbox v-if="stored?.pushover_app_token_configured" v-model="form.clear_pushover_app_token" label="Gespeicherten App-Token entfernen" density="compact" />
        <v-text-field v-model="form.pushover_user_key" type="password" autocomplete="new-password" label="User Key / Group Key" :placeholder="stored?.pushover_user_key_configured ? 'Gespeichert – leer lassen zum Beibehalten' : 'Benutzer-Schlüssel eingeben'" :disabled="form.clear_pushover_user_key" />
        <v-checkbox v-if="stored?.pushover_user_key_configured" v-model="form.clear_pushover_user_key" label="Gespeicherten Benutzer-Schlüssel entfernen" density="compact" />
        <v-text-field v-model="form.pushover_device" label="Gerätename (optional)" hint="Leer = alle Geräte dieses Benutzers. Mehrere Namen mit Komma trennen." persistent-hint />
        <v-btn type="button" class="mt-4" variant="tonal" :disabled="busy || !stored" :loading="testing === 'pushover'" @click="test('pushover')">Testnachricht senden</v-btn>
      </v-card-text></v-card></v-col>
      <v-col cols="12" lg="6"><v-card height="100%" title="ntfy" prepend-icon="mdi-message-badge-outline"><v-card-text>
        <v-switch v-model="form.ntfy_enabled" label="ntfy verwenden" color="primary" inset />
        <v-text-field v-model="form.ntfy_url" label="ntfy-Server" hint="Eigener Docker-Server oder https://ntfy.sh" persistent-hint />
        <v-text-field v-model="form.ntfy_topic" label="Topic" hint="Dieses Topic in der ntfy-App auf demselben Server abonnieren." persistent-hint class="mt-3" />
        <v-text-field v-model="form.ntfy_access_token" type="password" autocomplete="new-password" label="Access Token (optional)" :placeholder="stored?.ntfy_access_token_configured ? 'Gespeichert – leer lassen zum Beibehalten' : 'Token für ein geschütztes Topic'" :disabled="form.clear_ntfy_access_token" />
        <v-checkbox v-if="stored?.ntfy_access_token_configured" v-model="form.clear_ntfy_access_token" label="Gespeicherten ntfy-Token entfernen" density="compact" />
        <v-alert v-if="!form.ntfy_access_token && (!stored?.ntfy_access_token_configured || form.clear_ntfy_access_token)" type="info" variant="tonal" density="compact">Ohne Zugriffsschutz kann jeder mit Kenntnis des Topics Nachrichten mitlesen oder senden. Verwende für private Erinnerungen ein geschütztes Topic.</v-alert>
        <v-alert v-if="form.ntfy_url.startsWith('http://')" type="info" variant="tonal" density="compact" class="mt-3">HTTP überträgt Token und Nachrichten unverschlüsselt. Nur in einem vertrauenswürdigen lokalen Netz verwenden.</v-alert>
        <v-btn type="button" class="mt-4" variant="tonal" :disabled="busy || !stored" :loading="testing === 'ntfy'" @click="test('ntfy')">Testnachricht senden</v-btn>
      </v-card-text></v-card></v-col></v-row>
      <p class="text-medium-emphasis my-4">Testnachrichten verwenden die aktuellen Eingaben, speichern sie aber nicht. Beide Dienste können gleichzeitig aktiv sein.</p>
      </fieldset>
      <div class="push-save-bar d-flex align-center flex-wrap ga-3 pa-3"><span>{{ dirty ? 'Ungespeicherte Änderungen' : 'Keine offenen Änderungen' }}</span><v-spacer /><v-btn type="button" :disabled="busy || !dirty" @click="discard">Verwerfen</v-btn><v-btn type="submit" color="primary" :disabled="busy || !stored" :loading="saving">Speichern</v-btn></div>
    </v-form>
    <v-card title="Letzte Versandversuche" class="mt-5"><v-card-text>
      <v-btn variant="text" prepend-icon="mdi-refresh" :disabled="busy" @click="refreshHistory().catch(() => { error = 'Versandstatus konnte nicht geladen werden' })">Status aktualisieren</v-btn>
      <p v-if="!history.length" class="text-medium-emphasis mt-3">Noch keine Versandversuche.</p>
      <v-list v-else lines="three"><v-list-item v-for="(entry, index) in history" :key="index" :title="`${entry.provider === 'pushover' ? 'Pushover' : 'ntfy'} · ${entry.kind === 'test' ? 'Test' : 'Tägliche Erinnerung'} · ${statusName(entry.status)}`" :subtitle="`${timestamp(entry.last_attempt_at)} · Versuch ${entry.attempts} · ${entry.detail || ''}${entry.next_retry_at ? ' · Nächster Versuch: ' + timestamp(entry.next_retry_at) : ''}`" /></v-list>
      <p class="text-medium-emphasis mt-3">„Angenommen“ bestätigt den Empfang beim Push-Dienst, nicht das Lesen auf deinem Smartphone. Automatische Fehler werden bis zu dreimal im Abstand von 15 Minuten versucht.</p>
    </v-card-text></v-card>
  </v-container>
</template>
<style scoped>
.push-settings { max-width: 1300px; }
.push-fields { border: 0; padding: 0; min-width: 0; }
.push-save-bar { position: sticky; bottom: 0; z-index: 3; background: rgb(var(--v-theme-surface)); border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
</style>
