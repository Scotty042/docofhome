<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { consumptionApi } from '../services/consumptionApi'
import type { ConsumptionMeter } from '../types/consumption'
import { consumptionMeterTypeIcons, consumptionMeterTypeLabels } from '../types/consumption'

const props = defineProps<{
  assetId?: string
  locationId?: string
  title?: string
}>()

const meters = ref<ConsumptionMeter[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

function formatNumber(value: number | null, decimals: number): string {
  return value === null
    ? 'Noch keine Ablesung'
    : value.toLocaleString('de-DE', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })
}

async function load() {
  if (!props.assetId && !props.locationId) return
  loading.value = true
  error.value = null
  try {
    meters.value = await consumptionApi.meters({
      asset_id: props.assetId,
      location_id: props.locationId
    })
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Verknüpfte Zähler konnten nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

watch(() => [props.assetId, props.locationId], () => void load())
onMounted(() => void load())
</script>

<template>
  <v-card :title="title || 'Verbrauchszähler'" prepend-icon="mdi-chart-line" class="mb-5">
    <v-progress-linear v-if="loading" indeterminate color="primary" />
    <v-alert v-if="error" type="warning" variant="tonal" density="compact" class="ma-4">{{ error }}</v-alert>
    <v-list v-else-if="meters.length" lines="two">
      <v-list-item
        v-for="meter in meters"
        :key="meter.id"
        :prepend-icon="consumptionMeterTypeIcons[meter.meter_type]"
        :title="meter.name"
        :subtitle="`${consumptionMeterTypeLabels[meter.meter_type]} · ${formatNumber(meter.latest_value, meter.decimals)}${meter.latest_value === null ? '' : ` ${meter.unit}`}`"
        :to="{ path: '/consumption', query: { meter: meter.id, tab: 'meters' } }"
      >
        <template #append>
          <v-chip v-if="meter.due_for_reading" size="x-small" color="warning" variant="tonal">Fällig</v-chip>
          <v-icon v-else icon="mdi-arrow-right" size="small" />
        </template>
      </v-list-item>
    </v-list>
    <v-card-text v-else-if="!loading && !error" class="text-medium-emphasis">
      Noch kein Verbrauchszähler zugeordnet.
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn variant="text" prepend-icon="mdi-chart-line" to="/consumption">Verbrauch öffnen</v-btn>
    </v-card-actions>
  </v-card>
</template>
