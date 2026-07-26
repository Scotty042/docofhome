<script setup lang="ts">
interface IconOption {
  title: string
  value: string
}

defineProps<{ modelValue: string | null }>()
const emit = defineEmits<{ 'update:modelValue': [value: string | null] }>()

const iconOptions: IconOption[] = [
  { title: 'Allgemeines Gerät', value: 'mdi-devices' },
  { title: 'Elektrische Verteilung', value: 'mdi-electric-switch' },
  { title: 'Schalter / Sicherungsautomat', value: 'mdi-toggle-switch' },
  { title: 'Schutzschalter', value: 'mdi-shield-outline' },
  { title: 'Kombinierter Schutz', value: 'mdi-shield-check' },
  { title: 'Stromzähler', value: 'mdi-meter-electric' },
  { title: 'Smart Meter', value: 'mdi-meter-electric-outline' },
  { title: 'Wechselrichter / Solar', value: 'mdi-solar-power-variant' },
  { title: 'Batteriespeicher', value: 'mdi-battery-high' },
  { title: 'Steckdose / Verbraucher', value: 'mdi-power-plug' },
  { title: 'Leuchte', value: 'mdi-lightbulb-outline' },
  { title: 'Sensor', value: 'mdi-access-point' },
  { title: 'Thermostat', value: 'mdi-thermostat' },
  { title: 'Heizung', value: 'mdi-radiator' },
  { title: 'Wasserpumpe', value: 'mdi-water-pump' },
  { title: 'Lüfter', value: 'mdi-fan' },
  { title: 'Router', value: 'mdi-router-network' },
  { title: 'Netzwerk', value: 'mdi-lan' },
  { title: 'Firewall / Sicherheit', value: 'mdi-security-network' },
  { title: 'Server', value: 'mdi-server' },
  { title: 'NAS', value: 'mdi-nas' },
  { title: 'Kamera', value: 'mdi-cctv' },
  { title: 'Tür', value: 'mdi-door' },
  { title: 'Fenster', value: 'mdi-window-closed-variant' },
  { title: 'Waschmaschine', value: 'mdi-washing-machine' },
  { title: 'Kühlschrank', value: 'mdi-fridge-outline' },
  { title: 'Geschirrspüler', value: 'mdi-dishwasher' },
  { title: 'Fernseher', value: 'mdi-television' },
  { title: 'Lautsprecher', value: 'mdi-speaker' },
  { title: '3D-Drucker', value: 'mdi-printer-3d-nozzle-outline' },
  { title: 'Saugroboter', value: 'mdi-robot-vacuum' },
  { title: 'Sonstige Form', value: 'mdi-shape-outline' }
]
</script>

<template>
  <v-autocomplete
    :model-value="modelValue"
    label="Symbol"
    :items="iconOptions"
    item-title="title"
    item-value="value"
    clearable
    hint="Das Symbol hilft, Asset-Typen in Listen und Auswahlen schneller zu erkennen."
    persistent-hint
    @update:model-value="emit('update:modelValue', $event || null)"
  >
    <template #item="{ props, item }">
      <v-list-item v-bind="props" :prepend-icon="item.raw.value" />
    </template>
    <template #selection="{ item }">
      <div class="d-flex align-center ga-2">
        <v-icon :icon="item.raw.value" />
        <span>{{ item.raw.title }}</span>
      </div>
    </template>
  </v-autocomplete>
</template>
