<script setup lang="ts">
import { intervalSeconds, formatDuration as duration, rangeOptions, quickRange, rangeBounds, localDateTime } from '../services/timeTracking'
import { computed, onMounted, onUnmounted, ref } from 'vue'
interface Interval { id: string; ticket: string; customer: string; info: string; started_at: number; ended_at: number | null; running: boolean; completed: boolean }
const items = ref<Interval[]>([])
const ticket = ref(''), customer = ref(''), info = ref(''), error = ref(''), busy = ref(false)
const now = ref(Date.now() / 1000)
const range = ref('30')
const initialRange = quickRange('30')
const from = ref(initialRange[0]), to = ref(initialRange[1])
const active = computed(() => items.value.find(i => i.running))
const bounds = computed(() => rangeBounds(from.value, to.value))
function selectRange(value: string) {
  range.value = value
  if (value !== 'custom') [from.value, to.value] = quickRange(value)
}
function seconds(i: Interval) {
  return bounds.value ? intervalSeconds(i.started_at, i.ended_at ?? now.value, bounds.value[0], bounds.value[1]) : 0
}
const visible = computed(() => items.value.filter(i => bounds.value && i.started_at < bounds.value[1] && (i.ended_at ?? now.value) > bounds.value[0]))
const groups = computed(() => {
  const result = new Map<string, { ticket: string; total: number; slots: Interval[] }>()
  for (const i of visible.value) {
    const g = result.get(i.ticket) ?? { ticket: i.ticket, total: 0, slots: [] }
    g.total += seconds(i); g.slots.push(i); result.set(i.ticket, g)
  }
  return [...result.values()]
})
const total = computed(() => visible.value.reduce((sum, i) => sum + seconds(i), 0))
const recent = computed(() => [...new Map(items.value.map(i => [i.ticket, i])).keys()].map(t => items.value.find(i => i.ticket === t)!))
const stamp = (value: number) => new Date(value*1000).toLocaleString('de-DE')
async function request(path = '', body?: unknown, method = 'POST'): Promise<unknown> {
  const response = await fetch(`/api/v1/time-tracking${path}`, body === undefined ? undefined : { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((d: { msg: string }) => d.msg.replace('Value error, ', '')).join(' ') : 'Zeiterfassung konnte nicht geladen oder gespeichert werden.')
  }
  return response.json()
}
async function load() { items.value = await request() as Interval[] }
async function act(path: string, body: unknown = {}) {
  busy.value = true; error.value = ''
  try { await request(path, body); await load() }
  catch (e) { error.value = e instanceof Error ? e.message : String(e); try { await load() } catch { /* retain last known data */ } }
  finally { busy.value = false }
}
function resume(i: Interval) {
  ticket.value = i.ticket; customer.value = i.customer; info.value = i.info
  void act('/start', { ticket: i.ticket, customer: i.customer, info: i.info })
}
const editor = ref(false), editingId = ref<string | null>(null), editError = ref('')
const draft = ref({ ticket: '', customer: '', info: '', start: '', end: '' })
function openEditor(slot?: Interval) {
  editingId.value = slot?.id ?? null
  draft.value = { ticket: slot?.ticket ?? '', customer: slot?.customer ?? '', info: slot?.info ?? '',
    start: slot ? localDateTime(slot.started_at) : '', end: slot?.ended_at ? localDateTime(slot.ended_at) : '' }
  editError.value = ''; editor.value = true
}
async function saveInterval() {
  busy.value = true; editError.value = ''
  try {
    const body = { ticket: draft.value.ticket, customer: draft.value.customer, info: draft.value.info,
      started_at: new Date(draft.value.start).toISOString(), ended_at: new Date(draft.value.end).toISOString() }
    await request(editingId.value ? `/${editingId.value}` : '/manual', body, editingId.value ? 'PUT' : 'POST')
    editor.value = false
    try { await load() } catch { error.value = 'Eintrag gespeichert; Ansicht konnte nicht aktualisiert werden.' }
  } catch (e) { editError.value = e instanceof Error ? e.message : String(e) }
  finally { busy.value = false }
}
async function refresh() {
  busy.value = true; error.value = ''
  try { await load() } catch (e) { error.value = String(e) } finally { busy.value = false }
}
let tick: ReturnType<typeof setInterval> | undefined
let poll: ReturnType<typeof setInterval> | undefined
onMounted(async () => {
  tick = setInterval(() => { now.value = Date.now()/1000 }, 1000)
  poll = setInterval(() => { void load().catch(() => { error.value = 'Verbindung unterbrochen. Bitte aktualisieren.' }) }, 15000)
  try { await load() } catch (e) { error.value = String(e) }
})
onUnmounted(() => { clearInterval(tick); clearInterval(poll) })
</script>

<template>
  <v-container>
    <h1 class="text-h4 mb-4">Zeiterfassung</h1>
    <v-alert v-if="error" type="error" class="mb-4" role="alert">{{ error }}</v-alert>
    <v-card v-if="active" class="mb-4" title="Laufende Tätigkeit">
      <v-card-text>
        <strong>{{ active.ticket }} · {{ active.customer }}</strong>
        <p>{{ active.info }}</p>
        <p>Beginn: {{ stamp(active.started_at) }}</p>
        <p class="text-h5 my-3" aria-live="off">{{ duration(now - active.started_at) }}</p>
        <v-btn :disabled="busy" class="mr-2" @click="act(`/${active.id}/pause`)">Pause</v-btn>
        <v-btn color="primary" :disabled="busy" @click="act(`/${active.id}/end`)">Ende</v-btn>
      </v-card-text>
    </v-card>
    <v-card title="Neue Tätigkeit" class="mb-4">
      <v-card-text>
        <v-form @submit.prevent="act('/start', { ticket, customer, info })">
          <v-text-field v-model="ticket" label="Ticketnummer" maxlength="100" required :disabled="!!active || busy" />
          <v-text-field v-model="customer" label="Kundenname" maxlength="200" required :disabled="!!active || busy" />
          <v-textarea v-model="info" label="Weitere Info" maxlength="4000" rows="2" :disabled="!!active || busy" />
          <v-btn type="submit" color="primary" :disabled="busy || !!active || !ticket.trim() || !customer.trim()">Start</v-btn>
        </v-form>
      </v-card-text>
    </v-card>
    <v-card v-if="recent.length" title="Tickets wieder aufnehmen" class="mb-4">
      <v-card-text class="d-flex flex-wrap ga-2">
        <v-btn v-for="i in recent" :key="i.ticket" :disabled="busy || !!active" @click="resume(i)">{{ i.ticket }} · {{ i.customer }}</v-btn>
      </v-card-text>
    </v-card>
    <v-card title="Verlauf">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4"><v-select :model-value="range" :items="rangeOptions" label="Zeitraum" @update:model-value="selectRange" /></v-col>
          <v-col cols="12" sm="6" md="4"><v-text-field v-model="from" type="date" label="Von" @update:model-value="range = 'custom'" /></v-col>
          <v-col cols="12" sm="6" md="4"><v-text-field v-model="to" type="date" label="Bis einschließlich" @update:model-value="range = 'custom'" /></v-col>
        </v-row>
        <div class="d-flex flex-wrap ga-2 mb-4">
          <v-btn :disabled="busy" @click="refresh">Aktualisieren</v-btn>
          <v-btn color="primary" :disabled="busy" @click="openEditor()">Manuellen Eintrag hinzufügen</v-btn>
        </div>
        <v-alert v-if="!bounds" type="warning" class="mb-4">Bitte einen gültigen Zeitraum wählen. Von darf nicht nach Bis liegen.</v-alert>
      </v-card-text>
      <v-card-text>
        <p class="text-h5 mb-4">Gesamtzeit im Zeitraum: {{ duration(total) }}</p>
        <p v-if="!groups.length">In diesem Zeitraum sind keine Arbeitszeiten vorhanden.</p>
        <div class="d-flex flex-wrap ga-2 mb-4" aria-label="Ticketsummen">
          <v-chip v-for="group in groups" :key="group.ticket">{{ group.ticket }} · {{ duration(group.total) }}</v-chip>
        </div>
        <v-table v-if="visible.length" class="history-table">
          <thead><tr><th>Ticketnummer</th><th>Kundenname / weitere Info</th><th>Anfang</th><th>Ende</th><th>Dauer im Zeitraum</th><th>Status</th><th>Aktionen</th></tr></thead>
          <tbody>
            <tr v-for="slot in visible" :key="slot.id">
              <td>{{ slot.ticket }}</td>
              <td><strong>{{ slot.customer }}</strong><p class="history-info">{{ slot.info }}</p></td>
              <td class="text-no-wrap">{{ stamp(slot.started_at) }}</td>
              <td class="text-no-wrap">{{ slot.ended_at === null ? 'läuft' : stamp(slot.ended_at) }}</td>
              <td>{{ duration(seconds(slot)) }}</td>
              <td>{{ slot.running ? 'Läuft' : slot.completed ? 'Beendet' : 'Pausiert' }}</td>
              <td><v-btn v-if="!slot.running" variant="text" :disabled="busy" :aria-label="`Arbeitslauf ${slot.ticket} vom ${stamp(slot.started_at)} bearbeiten`" @click="openEditor(slot)">Bearbeiten</v-btn></td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>
    <v-dialog v-model="editor" max-width="640" :persistent="busy">
      <v-card :title="editingId ? 'Arbeitslauf bearbeiten' : 'Manueller Arbeitslauf'">
        <v-form @submit.prevent="saveInterval">
          <v-card-text>
            <v-alert v-if="editError" type="error" class="mb-4" role="alert">{{ editError }}</v-alert>
            <v-text-field v-model="draft.ticket" label="Ticketnummer" maxlength="100" required :disabled="busy" />
            <v-text-field v-model="draft.customer" label="Kundenname" maxlength="200" required :disabled="busy" />
            <v-textarea v-model="draft.info" label="Weitere Info" maxlength="4000" rows="2" :disabled="busy" />
            <v-text-field v-model="draft.start" type="datetime-local" step="1" label="Anfangszeit" required :disabled="busy" />
            <v-text-field v-model="draft.end" type="datetime-local" step="1" label="Endzeit" required :disabled="busy" />
            <p>Zeiten in deiner lokalen Zeitzone. Ende muss nach Anfang liegen; Arbeitsläufe dürfen sich nicht überschneiden.</p>
          </v-card-text>
          <v-card-actions>
            <v-btn :disabled="busy" @click="editor = false">Abbrechen</v-btn>
            <v-spacer />
            <v-btn type="submit" color="primary" :loading="busy" :disabled="!draft.ticket.trim() || !draft.customer.trim() || !draft.start || !draft.end">Speichern</v-btn>
          </v-card-actions>
        </v-form>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<style scoped>
.history-table { overflow-x: auto; }
.history-info { white-space: pre-wrap; overflow-wrap: anywhere; min-width: 180px; }
</style>
