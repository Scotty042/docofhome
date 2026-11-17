<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
interface Configuration { enabled: boolean; upload_to_nextcloud: boolean; nextcloud_folder: string }
interface State extends Configuration { last_exported_month: string | null; last_success_at: string | null; last_error: string | null }
interface ExportFile { filename: string; month: string; size_bytes: number }
const configuration = ref<State | null>(null), files = ref<ExportFile[]>([])
const form = ref<Configuration>({ enabled: false, upload_to_nextcloud: false, nextcloud_folder: 'DocOfHome/Zeiterfassung' })
const busy = ref(false), error = ref(''), notice = ref('')
const dirty = computed(() => configuration.value && (form.value.enabled !== configuration.value.enabled || form.value.upload_to_nextcloud !== configuration.value.upload_to_nextcloud || form.value.nextcloud_folder !== configuration.value.nextcloud_folder))
async function request<T>(path = '', body?: Configuration): Promise<T> {
  const response = await fetch(`/api/v1/time-exports${path}`, path === '/run' ? {method:'POST'} : body ? {method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : undefined)
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((d: {msg: string})=>d.msg).join(' ') : 'CSV-Export nicht verfügbar.')
  }
  return response.json()
}
async function load() {
  const data = await request<{configuration:State;files:ExportFile[]}>()
  configuration.value = data.configuration; files.value = data.files
  form.value = {enabled:data.configuration.enabled,upload_to_nextcloud:data.configuration.upload_to_nextcloud,nextcloud_folder:data.configuration.nextcloud_folder}
}
async function act(action: 'load' | 'save' | 'run') {
  busy.value = true; error.value = ''; notice.value = ''
  try {
    if (action === 'save') {
      await request<State>('/configuration',form.value)
      notice.value = 'Export-Einstellungen gespeichert.'
    }
    if (action === 'run') {
      const state = await request<State>('/run')
      if (!state.last_error) notice.value = 'CSV für den Vormonat erstellt.'
    }
    await load()
  } catch (e) { error.value = e instanceof Error ? e.message : String(e) }
  finally { busy.value = false }
}
onMounted(() => { void act('load') })
</script>
<template>
  <v-expansion-panels class="mt-4">
    <v-expansion-panel title="Monatlicher CSV-Export">
      <v-expansion-panel-text>
        <v-alert v-if="error" type="error" role="alert" class="mb-3">{{ error }}</v-alert>
        <v-alert v-if="configuration?.last_error" type="error" role="alert" class="mb-3">{{ configuration.last_error }} Eine bereits erzeugte lokale CSV bleibt unten verfügbar.</v-alert>
        <v-alert v-if="notice" type="success" class="mb-3">{{ notice }}</v-alert>
        <p class="mb-3">Exportiert den abgeschlossenen Vormonat automatisch in der eingestellten Zeitzone. Die CSV enthält Tätigkeit, Kunde, Info, Anfang, Ende, Dauer und BCS. Lokale Dateien kannst du hier herunterladen.</p>
        <v-checkbox v-model="form.enabled" label="Monatlichen CSV-Export aktivieren" :disabled="busy || !configuration" hide-details />
        <v-checkbox v-model="form.upload_to_nextcloud" label="CSV zusätzlich nach Nextcloud hochladen" :disabled="busy || !configuration" hide-details />
        <v-text-field v-if="form.upload_to_nextcloud" v-model="form.nextcloud_folder" label="Nextcloud-Zielordner" hint="Relativ zum Benutzerverzeichnis" persistent-hint :disabled="busy" class="mt-3" maxlength="500" />
        <p v-if="configuration?.last_exported_month" class="mt-3">Zuletzt automatisch exportierter Monat: {{ configuration.last_exported_month }}</p>
        <p v-if="configuration?.last_success_at">Letzter erfolgreicher Lauf: {{ new Date(configuration.last_success_at).toLocaleString('de-DE') }}</p>
        <div class="d-flex flex-wrap ga-2 my-4">
          <v-btn color="primary" :disabled="busy || !dirty" @click="act('save')">Einstellungen speichern</v-btn>
          <v-btn :disabled="busy || !!dirty || !configuration" @click="act('run')">Vormonat jetzt exportieren</v-btn>
          <v-btn :disabled="busy || !!dirty" @click="act('load')">Aktualisieren</v-btn>
        </div>
        <p v-if="dirty">Bitte die Einstellungen vor dem Export speichern.</p>
        <p>„Vormonat jetzt exportieren“ erstellt dessen CSV erneut, auch bei ausgeschalteter Automatik. Es verwendet die gespeicherte Nextcloud-Einstellung. Spätere Zeitkorrekturen werden so in die Datei übernommen.</p>
        <v-list v-if="files.length" aria-label="Monatliche CSV-Dateien">
          <v-list-item v-for="file in files" :key="file.filename" :title="file.month">
            <template #append><v-btn variant="text" :href="`/api/v1/time-exports/${encodeURIComponent(file.filename)}/download`" :download="file.filename">CSV herunterladen</v-btn></template>
          </v-list-item>
        </v-list>
        <p v-else class="mt-3">Noch keine monatlichen CSV-Dateien vorhanden.</p>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>
