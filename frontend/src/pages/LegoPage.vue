<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import ProductImageField from '../components/ProductImageField.vue'
import { legoApi } from '../services/legoApi'
import { locationApi } from '../services/locationApi'
import { useNotificationStore } from '../stores/notifications'
import { buildStatuses, editableLegoSet, emptyLegoSet, legoDimensions } from '../types/lego'
import type { LegoDashboard, LegoSet } from '../types/lego'
import type { LocationTreeNode } from '../types/locations'

const notifications = useNotificationStore()
const items = ref<LegoSet[]>([])
const dashboard = ref<LegoDashboard | null>(null)
const locations = ref<{ title: string, value: string }[]>([])
const query = ref('')
const status = ref<string | null>(null)
const theme = ref<string | null>(null)
const location = ref<string | null>(null)
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const editor = ref(false)
const editingId = ref<string | null>(null)
const form = ref(emptyLegoSet())
const baseline = ref('')
const selected = ref<LegoSet | null>(null)
const deleting = ref<LegoSet | null>(null)
const imageFailures = ref(new Set<string>())
const dirty = computed(() => editor.value && JSON.stringify(form.value) !== baseline.value)
const themes = computed(() => [...new Set(items.value.map(s => s.theme).filter(Boolean))].sort())
const visible = computed(() => items.value.filter(s => (!query.value.trim() || [s.name, s.set_number, s.theme, s.location_name, s.storage_note].join(' ').toLocaleLowerCase().includes(query.value.trim().toLocaleLowerCase())) && (!status.value || s.build_status === status.value) && (!theme.value || s.theme === theme.value) && (!location.value || s.location_id === location.value)))
const money = (value: string | number | null) => value === null ? 'Preis nicht erfasst' : new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(Number(value))
const number = (value: number) => value.toLocaleString('de-DE')
const statusTitle = (value: string) => buildStatuses.find(s => s.value === value)?.title ?? value
const yesNo = (value: boolean | null) => value === null ? 'Unbekannt' : value ? 'Ja' : 'Nein'
const booleanOptions = [{ title: 'Unbekannt', value: null }, { title: 'Ja', value: true }, { title: 'Nein', value: false }]
async function load() {
  loading.value = true
  try {
    const [sets, totals] = await Promise.all([legoApi.list(), legoApi.dashboard()])
    items.value = sets; dashboard.value = totals; error.value = ''
  } catch (e) { error.value = e instanceof Error ? e.message : 'Sammlung konnte nicht geladen werden' }
  finally { loading.value = false }
}
function flatten(nodes: LocationTreeNode[]): { title: string, value: string }[] {
  return nodes.flatMap((n): { title: string, value: string }[] => [{ title: n.path || n.name, value: n.id }, ...flatten(n.children)])
}
onMounted(async () => {
  await load()
  try { locations.value = flatten(await locationApi.tree()) }
  catch { notifications.warning('Lagerorte konnten nicht geladen werden. Freitext-Lagerung ist weiterhin möglich.') }
})
function open(set?: LegoSet) {
  selected.value = null; editingId.value = set?.id ?? null
  form.value = set ? editableLegoSet(set) : emptyLegoSet()
  baseline.value = JSON.stringify(form.value); error.value = ''; editor.value = true
}
function close() {
  if (busy.value || (dirty.value && !window.confirm('Ungespeicherte LEGO-Angaben verwerfen?'))) return
  editor.value = false
}
async function save() {
  busy.value = true
  try {
    const payload = { ...form.value }
    for (const key of ['release_year', 'parts_count', 'width_cm', 'depth_cm', 'height_cm'] as const) {
      const value = payload[key]
      payload[key] = value === null || String(value) === '' ? null : Number(value)
    }
    payload.purchase_price = payload.purchase_price === '' ? null : payload.purchase_price
    payload.purchase_date ||= null; payload.researched_at ||= null
    if (editingId.value) await legoApi.update(editingId.value, payload)
    else await legoApi.create(payload)
    editor.value = false; await load()
    notifications.success('LEGO-Set gespeichert')
  } catch (e) { error.value = e instanceof Error ? e.message : 'Speichern fehlgeschlagen' }
  finally { busy.value = false }
}
async function remove() {
  if (!deleting.value) return
  busy.value = true
  try { await legoApi.remove(deleting.value.id); deleting.value = null; selected.value = null; await load() }
  catch (e) { error.value = e instanceof Error ? e.message : 'Löschen fehlgeschlagen' }
  finally { busy.value = false }
}
function leave(event: BeforeUnloadEvent) { if (dirty.value) { event.preventDefault(); event.returnValue = '' } }
window.addEventListener('beforeunload', leave)
onBeforeUnmount(() => window.removeEventListener('beforeunload', leave))
onBeforeRouteLeave(() => !busy.value && (!dirty.value || window.confirm('Ungespeicherte LEGO-Angaben verwerfen und die Seite verlassen?')))
</script>

<template>
  <v-container class="lego-page py-6" fluid>
    <div class="d-flex flex-wrap align-center ga-3 mb-5">
      <div><h1>Meine LEGO-Sammlung</h1><p class="text-medium-emphasis">Sets, Kaufkosten und Lagerorte auf einen Blick.</p></div>
      <v-spacer /><v-btn variant="text" to="/wiki/handbuch" prepend-icon="mdi-book-open-page-variant">Handbuch</v-btn>
      <v-btn variant="text" icon="mdi-refresh" aria-label="Sammlung aktualisieren" :loading="loading" @click="load" />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="open()">Set erfassen</v-btn>
    </div>
    <v-alert v-if="error && !editor" type="error" class="mb-4">{{ error }}</v-alert>
    <v-row v-if="dashboard" class="mb-4">
      <v-col cols="12" md="4"><v-card rounded="lg"><v-card-text><div>Sets in deiner Sammlung</div><div class="text-h4 my-2">{{ number(dashboard.sets_count) }}</div><div class="text-medium-emphasis">Jede Setnummer einmal</div></v-card-text></v-card></v-col>
      <v-col cols="12" md="4"><v-card rounded="lg"><v-card-text><div>Gesamte Kaufkosten</div><div class="text-h4 my-2">{{ money(dashboard.purchase_total) }}</div><div class="text-medium-emphasis">{{ dashboard.missing_prices ? `${dashboard.missing_prices} Kaufpreise fehlen` : 'Alle Kaufpreise erfasst' }} · EUR</div></v-card-text></v-card></v-col>
      <v-col cols="12" md="4"><v-card rounded="lg"><v-card-text><div>Teile insgesamt</div><div class="text-h4 my-2">{{ number(dashboard.parts_total) }}</div><div class="text-medium-emphasis">{{ dashboard.missing_parts ? `${dashboard.missing_parts} Teilezahlen fehlen` : 'Alle Teilezahlen erfasst' }}</div></v-card-text></v-card></v-col>
    </v-row>
    <v-row dense class="mb-4">
      <v-col cols="12" md="4"><v-text-field v-model="query" label="Setnummer, Name oder Lagerort suchen" prepend-inner-icon="mdi-magnify" hide-details clearable @click:clear="query = ''" /></v-col>
      <v-col cols="12" sm="4" md="2"><v-select v-model="status" :items="buildStatuses" label="Aufbaustatus" clearable hide-details /></v-col>
      <v-col cols="12" sm="4" md="3"><v-select v-model="theme" :items="themes" label="Themenwelt" clearable hide-details /></v-col>
      <v-col cols="12" sm="4" md="3"><v-select v-model="location" :items="locations" label="Lagerort" clearable hide-details /></v-col>
    </v-row>
    <p class="text-medium-emphasis mb-4">{{ visible.length }} von {{ items.length }} Sets · Kennzahlen beziehen sich auf die gesamte Sammlung.</p>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />
    <v-card v-if="!loading && !visible.length" variant="tonal" class="pa-6 text-center"><v-icon size="48">mdi-toy-brick-outline</v-icon><h2 class="mt-3">{{ items.length ? 'Keine passenden Sets' : 'Deine Sammlung beginnt hier' }}</h2><p class="my-3">{{ items.length ? 'Passe deine Suche oder Filter an.' : 'Erfasse eine Setnummer manuell oder lass ein recherchiertes Set über MCP eintragen.' }}</p><v-btn v-if="!items.length" color="primary" @click="open()">Erstes Set erfassen</v-btn></v-card>
    <v-row>
      <v-col v-for="set in visible" :key="set.id" cols="12" sm="6" lg="4" xl="3">
        <v-card rounded="lg" height="100%" @click="selected = set" tabindex="0" role="button" :aria-label="`${set.set_number}: ${set.name} anzeigen`" @keydown.enter="selected = set" @keydown.space.prevent="selected = set">
          <v-img v-if="set.image_url && !imageFailures.has(set.id)" :src="set.image_url" height="190" contain class="bg-surface-variant" @error="imageFailures.add(set.id)" />
          <div v-else class="lego-placeholder bg-surface-variant"><v-icon size="64" color="primary">mdi-toy-brick-outline</v-icon><span class="text-medium-emphasis">Kein Setbild</span></div>
          <v-card-text><div class="text-medium-emphasis">{{ set.set_number }}{{ set.theme ? ` · ${set.theme}` : '' }}</div><h2 class="text-h6 mt-1 mb-2">{{ set.name }}</h2><v-chip size="small" class="mb-3">{{ statusTitle(set.build_status) }}</v-chip><div>{{ set.location_name || 'Kein Lagerort' }}{{ set.storage_note ? ` · ${set.storage_note}` : '' }}</div><div class="mt-2">{{ money(set.purchase_price) }} · {{ set.parts_count === null ? 'Teilezahl fehlt' : `${number(set.parts_count)} Teile` }}</div><div class="text-medium-emphasis mt-1">{{ legoDimensions(set) }}</div></v-card-text>
          <v-card-actions><v-btn variant="text" @click.stop="open(set)">Bearbeiten</v-btn><v-spacer /><v-btn icon="mdi-delete-outline" variant="text" aria-label="Set löschen" @click.stop="deleting = set" /></v-card-actions>
        </v-card>
      </v-col>
    </v-row>
    <v-dialog :model-value="editor" max-width="960" persistent>
      <v-card><v-card-title>{{ editingId ? 'LEGO-Set bearbeiten' : 'LEGO-Set erfassen' }}</v-card-title>
        <v-form @submit.prevent="save"><v-card-text>
          <v-alert v-if="error" type="error" class="mb-4">{{ error }}</v-alert>
          <v-row dense><v-col cols="12" sm="4"><v-text-field v-model="form.set_number" label="Setnummer *" hint="10305 und 10305-1 gelten als dasselbe Set" persistent-hint required maxlength="30" /></v-col><v-col cols="12" sm="8"><v-text-field v-model="form.name" label="Name *" required maxlength="200" /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model="form.theme" label="Themenwelt" maxlength="100" /></v-col><v-col cols="6" sm="4"><v-text-field v-model.number="form.release_year" type="number" label="Erscheinungsjahr" min="1949" max="2200" /></v-col><v-col cols="6" sm="4"><v-text-field v-model.number="form.parts_count" type="number" label="Teilezahl" min="0" step="1" /></v-col>
          </v-row>
          <ProductImageField v-model="form.image_url" :search-terms="`LEGO ${form.set_number} ${form.name}`" title="Setbild" />
          <h3 class="mt-5 mb-3">Dein Set</h3><v-row dense>
            <v-col cols="12" sm="6"><v-select v-model="form.location_id" :items="locations" label="Lagerort" clearable /></v-col><v-col cols="12" sm="6"><v-text-field v-model="form.storage_note" label="Lagerung / Box / Regal" maxlength="300" /></v-col>
            <v-col cols="12" sm="6"><v-select v-model="form.build_status" :items="buildStatuses" label="Aufbaustatus" /></v-col><v-col cols="12" sm="6"><v-text-field v-model="form.condition" label="Zustand (z. B. sehr gut)" maxlength="100" /></v-col>
            <v-col cols="12" sm="4"><v-select v-model="form.complete" :items="booleanOptions" label="Vollständig" /></v-col><v-col cols="12" sm="4"><v-select v-model="form.box_present" :items="booleanOptions" label="Originalkarton vorhanden" /></v-col><v-col cols="12" sm="4"><v-select v-model="form.instructions_present" :items="booleanOptions" label="Anleitung vorhanden" /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model="form.purchase_price" type="number" label="Kaufpreis (EUR)" min="0" step="0.01" /></v-col><v-col cols="12" sm="4"><v-text-field v-model="form.purchase_date" type="date" label="Kaufdatum" clearable /></v-col><v-col cols="12" sm="4"><v-text-field v-model="form.seller" label="Händler" maxlength="200" /></v-col>
          </v-row>
          <h3 class="mt-3 mb-3">Maße des aufgebauten Modells (optional)</h3><v-row dense><v-col cols="4"><v-text-field v-model.number="form.width_cm" type="number" label="Breite (cm)" min="0.01" step="any" /></v-col><v-col cols="4"><v-text-field v-model.number="form.depth_cm" type="number" label="Tiefe (cm)" min="0.01" step="any" /></v-col><v-col cols="4"><v-text-field v-model.number="form.height_cm" type="number" label="Höhe (cm)" min="0.01" step="any" /></v-col><v-col cols="12"><v-text-field v-model="form.dimensions_note" label="Hinweis zu den Maßen (z. B. Flügel ausgeklappt)" maxlength="500" /></v-col></v-row>
          <v-row dense><v-col cols="12" sm="8"><v-text-field v-model="form.source_url" label="Quelle der recherchierten Angaben (URL)" clearable /></v-col><v-col cols="12" sm="4"><v-text-field v-model="form.researched_at" type="date" label="Recherchiert am" clearable /></v-col></v-row>
          <v-textarea v-model="form.notes" label="Notizen (z. B. separater Lagerort von Karton und Anleitung)" maxlength="50000" />
          <p class="text-medium-emphasis">Online recherchierte Daten können über MCP eingetragen werden. Alle Angaben bleiben manuell bearbeitbar.</p>
        </v-card-text><v-card-actions class="lego-save-bar"><span v-if="dirty" class="text-medium-emphasis">Ungespeicherte Änderungen</span><v-spacer /><v-btn :disabled="busy" @click="close">{{ dirty ? 'Verwerfen' : 'Schließen' }}</v-btn><v-btn type="submit" color="primary" variant="flat" :loading="busy">Speichern</v-btn></v-card-actions></v-form>
      </v-card>
    </v-dialog>
    <v-dialog :model-value="!!selected" max-width="720" @update:model-value="value => { if (!value) selected = null }"><v-card v-if="selected"><v-card-title class="text-wrap">{{ selected.set_number }} · {{ selected.name }}</v-card-title><v-card-text>
      <v-img v-if="selected.image_url" :src="selected.image_url" height="240" contain />
      <v-list lines="two"><v-list-item title="Themenwelt / Jahr / Teile" :subtitle="`${selected.theme || '–'} · ${selected.release_year ?? '–'} · ${selected.parts_count ?? '–'} Teile`" /><v-list-item title="Lagerort" :subtitle="`${selected.location_name || 'Nicht zugeordnet'} · ${selected.storage_note}`" /><v-list-item title="Status / Zustand" :subtitle="`${statusTitle(selected.build_status)} · ${selected.condition || 'Nicht erfasst'}`" /><v-list-item title="Vollständig / Karton / Anleitung" :subtitle="`${yesNo(selected.complete)} / ${yesNo(selected.box_present)} / ${yesNo(selected.instructions_present)}`" /><v-list-item title="Kauf" :subtitle="`${money(selected.purchase_price)} · ${selected.purchase_date || 'Datum fehlt'} · ${selected.seller}`" /><v-list-item title="Modellmaße" :subtitle="`${legoDimensions(selected)} ${selected.dimensions_note}`" /></v-list>
      <p class="lego-notes">{{ selected.notes }}</p><p v-if="selected.source_url" class="mt-4"><a :href="selected.source_url" target="_blank" rel="noopener noreferrer">Quelle öffnen</a>{{ selected.researched_at ? ` · Recherche: ${selected.researched_at}` : '' }}</p>
    </v-card-text><v-card-actions><v-btn @click="selected = null">Schließen</v-btn><v-spacer /><v-btn color="primary" @click="open(selected)">Bearbeiten</v-btn></v-card-actions></v-card></v-dialog>
    <v-dialog :model-value="!!deleting" max-width="450" persistent><v-card><v-card-title>Set löschen?</v-card-title><v-card-text>{{ deleting?.set_number }} · {{ deleting?.name }} wird aus deiner Sammlung entfernt.</v-card-text><v-card-actions><v-btn :disabled="busy" @click="deleting = null">Abbrechen</v-btn><v-spacer /><v-btn color="error" :loading="busy" @click="remove">Löschen</v-btn></v-card-actions></v-card></v-dialog>
  </v-container>
</template>
<style scoped>
.lego-page { max-width: 1600px; }
.lego-placeholder { height: 190px; display: flex; flex-direction: column; justify-content: center; align-items: center; gap: 12px; }
.lego-save-bar { position: sticky; bottom: 0; background: rgb(var(--v-theme-surface)); border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); z-index: 2; flex-wrap: wrap; }
.lego-notes { white-space: pre-wrap; overflow-wrap: anywhere; }
</style>
