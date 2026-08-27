<script setup lang="ts">
import { moduleKeys, type ModuleKey } from '../types/settings'

interface ModuleOption {
  key: ModuleKey
  title: string
  icon: string
  description: string
}

const props = defineProps<{ modelValue?: ModuleKey[], mainMenuValue?: ModuleKey[] }>()
const emit = defineEmits<{ 'update:modelValue': [value: ModuleKey[]], 'update:mainMenuValue': [value: ModuleKey[]] }>()

const modules: ModuleOption[] = [
  {
    key: 'locations',
    title: 'Bereiche & Räume',
    icon: 'mdi-home-floor-0',
    description: 'Gebäude, Etagen, Räume, Schränke und Einbauorte verwalten.',
  },
  {
    key: 'electrical',
    title: 'Elektro',
    icon: 'mdi-flash',
    description: 'Verteilungen, Felder, Schutzgeräte und deren physische Position dokumentieren.',
  },
  {
    key: 'assets',
    title: 'Assets',
    icon: 'mdi-devices',
    description: 'Konkrete Geräte und Gegenstände mit Serien- und Inventarnummer erfassen.',
  },
  {
    key: 'master_data',
    title: 'Stammdaten',
    icon: 'mdi-database-cog-outline',
    description: 'Wiederverwendbare Asset-Typen, Produkte und Labels pflegen.',
  },
  {
    key: 'network',
    title: 'Netzwerk',
    icon: 'mdi-lan',
    description: 'Netzwerkgeräte, Schnittstellen, IP-Netze, VLANs und Verbindungen dokumentieren.',
  },
  {
    key: 'smart_home',
    title: 'Smart Home',
    icon: 'mdi-home-assistant',
    description: 'Home-Assistant-Entitäten, Livewerte und Automationen verwalten.'
  },
  {
    key: 'consumption',
    title: 'Verbrauch',
    icon: 'mdi-chart-line',
    description: 'Strom-, Wasser- und weitere Verbrauchswerte erfassen und auswerten.'
  },
  {
    key: 'wiki',
    title: 'Wiki',
    icon: 'mdi-book-open-page-variant',
    description: 'Hierarchische Wissensseiten und freie Hausdokumentation verwalten.',
  },
  {
    key: 'maintenance',
    title: 'Wartung & Aufgaben',
    icon: 'mdi-format-list-checks',
    description: 'Fälligkeiten, wiederkehrende Wartungen und Aufgaben verwalten.',
  },
  {
    key: 'quality',
    title: 'Dokumentationsqualität',
    icon: 'mdi-clipboard-check-outline',
    description: 'Fehlende Angaben, defekte Links und überfällige Arbeiten erkennen.',
  },
  {
    key: 'cookbook', title: 'Kochbuch', icon: 'mdi-chef-hat',
    description: 'Strukturierte Rezepte verwalten, suchen und drucken.'
  },
  {
    key: 'images',
    title: 'Bilder',
    icon: 'mdi-image-multiple-outline',
    description: 'Immich-Bilder durchsuchen und mit DocOfHome-Inhalten verknüpfen.',
  },
  {
    key: 'documents',
    title: 'Dokumente',
    icon: 'mdi-folder-outline',
    description: 'Dokumente über den konfigurierten Nextcloud-Speicher verwalten und verknüpfen.',
  },
  {
    key: 'workloads',
    title: 'Dienste & Container (Docker)',
    icon: 'mdi-docker',
    description: 'Logische Dienste, Container und deren Zuordnungen dokumentieren.',
  }
]

function enabled(key: ModuleKey): boolean {
  return (props.modelValue ?? moduleKeys).includes(key)
}

function inMainMenu(key: ModuleKey): boolean {
  return (props.mainMenuValue ?? props.modelValue ?? moduleKeys).includes(key)
}

function setEnabled(key: ModuleKey, value: boolean | null) {
  const selected = new Set(props.modelValue ?? moduleKeys)
  if (value) selected.add(key)
  else selected.delete(key)
  emit('update:modelValue', moduleKeys.filter((item) => selected.has(item)))
}

function setMainMenu(key: ModuleKey, value: boolean | null) {
  const selected = new Set(props.mainMenuValue ?? props.modelValue ?? moduleKeys)
  if (value) selected.add(key)
  else selected.delete(key)
  emit('update:mainMenuValue', moduleKeys.filter((item) => selected.has(item)))
}
</script>

<template>
  <v-card title="Module und Navigation" prepend-icon="mdi-view-grid-plus-outline">
    <v-card-text>
      <v-alert type="info" variant="tonal" density="compact" class="mb-4">
        „Aktiviert“ stellt die Funktion bereit. Ohne „Im Hauptmenü anzeigen“ erscheint ein
        aktives Modul unter „Sonstiges“. Deaktivieren löscht keine Daten.
      </v-alert>
      <v-list lines="three" bg-color="transparent">
        <v-list-item v-for="module in modules" :key="module.key" :prepend-icon="module.icon">
          <v-list-item-title class="d-flex align-center ga-2">
            {{ module.title }}
          </v-list-item-title>
          <v-list-item-subtitle>{{ module.description }}</v-list-item-subtitle>
          <template #append>
            <div class="d-flex flex-wrap ga-4 align-center"><v-switch
              :model-value="enabled(module.key)"
              color="primary"
              hide-details
              inset
              label="Aktiviert"
              :aria-label="`${module.title} aktivieren`"
              @update:model-value="setEnabled(module.key, $event)"
            />
            <v-switch :model-value="inMainMenu(module.key)" :disabled="!enabled(module.key)"
              color="primary" hide-details inset label="Im Hauptmenü anzeigen"
              @update:model-value="setMainMenu(module.key, $event)" /></div>
          </template>
        </v-list-item>
      </v-list>
    </v-card-text>
  </v-card>
</template>
