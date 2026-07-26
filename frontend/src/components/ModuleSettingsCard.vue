<script setup lang="ts">
import { moduleKeys, type ModuleKey } from '../types/settings'

interface ModuleOption {
  key: ModuleKey
  title: string
  icon: string
  description: string
  available: boolean
}

const props = defineProps<{ modelValue?: ModuleKey[] }>()
const emit = defineEmits<{ 'update:modelValue': [value: ModuleKey[]] }>()

const modules: ModuleOption[] = [
  {
    key: 'locations',
    title: 'Bereiche & Räume',
    icon: 'mdi-home-floor-0',
    description: 'Gebäude, Etagen, Räume, Schränke und Einbauorte verwalten.',
    available: true
  },
  {
    key: 'electrical',
    title: 'Elektro',
    icon: 'mdi-flash',
    description: 'Verteilungen, Felder, Schutzgeräte und deren physische Position dokumentieren.',
    available: true
  },
  {
    key: 'assets',
    title: 'Assets',
    icon: 'mdi-devices',
    description: 'Konkrete Geräte und Gegenstände mit Serien- und Inventarnummer erfassen.',
    available: true
  },
  {
    key: 'master_data',
    title: 'Stammdaten',
    icon: 'mdi-database-cog-outline',
    description: 'Wiederverwendbare Asset-Typen, Produkte und Labels pflegen.',
    available: true
  },
  {
    key: 'network',
    title: 'Netzwerk',
    icon: 'mdi-lan',
    description: 'Netzwerkgeräte, Schnittstellen, IP-Netze, VLANs und Verbindungen dokumentieren.',
    available: true
  },
  {
    key: 'smart_home',
    title: 'Smart Home',
    icon: 'mdi-home-assistant',
    description: 'Vorgesehener Bereich für Home-Assistant-Entitäten und Automationen.',
    available: false
  },
  {
    key: 'consumption',
    title: 'Verbrauch',
    icon: 'mdi-chart-line',
    description: 'Vorgesehener Bereich für Strom-, Wasser- und weitere Verbrauchswerte.',
    available: false
  },
  {
    key: 'wiki',
    title: 'Wiki',
    icon: 'mdi-book-open-page-variant',
    description: 'Hierarchische Wissensseiten und freie Hausdokumentation verwalten.',
    available: true
  },
  {
    key: 'maintenance',
    title: 'Wartung & Aufgaben',
    icon: 'mdi-format-list-checks',
    description: 'Fälligkeiten, wiederkehrende Wartungen und Aufgaben verwalten.',
    available: true
  },
  {
    key: 'quality',
    title: 'Dokumentationsqualität',
    icon: 'mdi-clipboard-check-outline',
    description: 'Fehlende Angaben, defekte Links und überfällige Arbeiten erkennen.',
    available: true
  }
]

function enabled(key: ModuleKey): boolean {
  return (props.modelValue ?? moduleKeys).includes(key)
}

function setEnabled(key: ModuleKey, value: boolean | null) {
  const selected = new Set(props.modelValue ?? moduleKeys)
  if (value) selected.add(key)
  else selected.delete(key)
  emit('update:modelValue', moduleKeys.filter((item) => selected.has(item)))
}
</script>

<template>
  <v-card title="Module und Navigation" prepend-icon="mdi-view-grid-plus-outline">
    <v-card-text>
      <v-alert type="info" variant="tonal" density="compact" class="mb-4">
        Die Schalter blenden Menüeinträge ein oder aus. Vorhandene Daten bleiben erhalten;
        direkte URLs werden in dieser ersten Ausbaustufe nicht gesperrt.
      </v-alert>
      <v-list lines="three" bg-color="transparent">
        <v-list-item v-for="module in modules" :key="module.key" :prepend-icon="module.icon">
          <v-list-item-title class="d-flex align-center ga-2">
            {{ module.title }}
            <v-chip v-if="!module.available" size="x-small" variant="tonal">In Vorbereitung</v-chip>
          </v-list-item-title>
          <v-list-item-subtitle>{{ module.description }}</v-list-item-subtitle>
          <template #append>
            <v-switch
              :model-value="enabled(module.key)"
              color="primary"
              hide-details
              inset
              :aria-label="`${module.title} im Menü anzeigen`"
              @update:model-value="setEnabled(module.key, $event)"
            />
          </template>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>
</template>
