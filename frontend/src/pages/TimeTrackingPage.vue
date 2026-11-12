<script setup lang="ts">
import { intervalSeconds, formatDuration as duration } from '../services/timeTracking'
import { computed, onMounted, onUnmounted, ref } from 'vue'
interface Interval { id: string; ticket: string; customer: string; info: string; started_at: number; ended_at: number | null; running: boolean; completed: boolean }
const items = ref<Interval[]>([])
const ticket = ref(''), customer = ref(''), info = ref(''), error = ref(''), busy = ref(false)
const now = ref(Date.now() / 1000)
const localDay = (d: Date) => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
const day = ref(localDay(new Date()))
const active = computed(() => items.value.find(i => i.running))
const bounds = computed(() => {
  const start = new Date(`${day.value}T00:00:00`)
  const end = new Date(start); end.setDate(end.getDate()+1)
  return [start.getTime()/1000, end.getTime()/1000]
})
function seconds(i: Interval) {
  return intervalSeconds(i.started_at, i.ended_at ?? now.value, bounds.value[0]!, bounds.value[1]!)
}
const visible = computed(() => items.value.filter(i => i.started_at < bounds.value[1]! && (i.ended_at ?? now.value) > bounds.value[0]!))
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
async function request(path = '', body?: unknown): Promise<unknown> {
  const response = await fetch(`/api/v1/time-tracking${path}`, body === undefined ? undefined : { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(typeof data.detail === 'string' ? data.detail : 'Zeiterfassung konnte nicht geladen oder gespeichert werden.')
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
    <v-card title="Tagesübersicht">
      <v-card-text>
        <v-text-field v-model="day" type="date" label="Tag" :clearable="false" />
        <p class="text-h5 mb-4">Gesamtzeit: {{ duration(total) }}</p>
        <p v-if="!groups.length">Für diesen Tag sind keine Arbeitszeiten vorhanden.</p>
        <v-expansion-panels multiple>
          <v-expansion-panel v-for="group in groups" :key="group.ticket">
            <v-expansion-panel-title>{{ group.ticket }} · {{ duration(group.total) }} · {{ group.slots.length }} Arbeitsläufe</v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-list>
                <v-list-item v-for="slot in group.slots" :key="slot.id" class="mb-3">
                  <strong>{{ slot.customer }}</strong><p>{{ slot.info }}</p>
                  <p>Beginn: {{ stamp(slot.started_at) }}</p>
                  <p>Ende: {{ slot.ended_at === null ? 'läuft' : stamp(slot.ended_at) }}</p>
                  <p>{{ duration(seconds(slot)) }} an diesem Tag · {{ slot.running ? 'Läuft' : slot.completed ? 'Beendet' : 'Pausiert' }}</p>
                </v-list-item>
              </v-list>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </v-card-text>
    </v-card>
  </v-container>
</template>
