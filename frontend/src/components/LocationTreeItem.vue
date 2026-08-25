<script setup lang="ts">
import { computed, ref } from 'vue'

import { locationTypeIcon, locationTypeLabel } from '../services/locationPresentation'
import type { LocationTreeNode } from '../types/locations'

defineOptions({ name: 'LocationTreeItem' })

const props = defineProps<{
  node: LocationTreeNode
  depth?: number
}>()

const expanded = ref((props.depth ?? 0) < 2)
const hasChildren = computed(() => props.node.children.length > 0)
const totalAssets = computed(() => (
  props.node.direct_asset_count + props.node.descendant_asset_count
))
</script>

<template>
  <div>
    <div
      class="location-tree-row d-flex align-center ga-2 py-1"
      :style="{ paddingLeft: `${(depth ?? 0) * 24}px` }"
    >
      <v-btn
        v-if="hasChildren"
        :icon="expanded ? 'mdi-chevron-down' : 'mdi-chevron-right'"
        size="x-small"
        variant="text"
        :aria-label="expanded ? 'Ebene einklappen' : 'Ebene ausklappen'"
        :title="expanded ? 'Ebene einklappen' : 'Ebene ausklappen'"
        @click="expanded = !expanded"
      />
      <span v-else class="tree-spacer" />
      <v-icon :icon="locationTypeIcon(node.location_type)" color="secondary" />
      <v-btn
        class="tree-link justify-start flex-grow-1"
        variant="text"
        :to="`/locations/${node.id}`"
      >
        <span class="text-left">
          <strong>{{ node.name }}</strong>
          <span class="text-caption text-medium-emphasis ml-2">
            {{ locationTypeLabel(node.location_type) }}
          </span>
        </span>
      </v-btn>
      <v-chip v-if="node.deleted_at" color="warning" size="x-small" variant="tonal">
        Archiviert
      </v-chip>
      <v-chip size="x-small" variant="outlined" prepend-icon="mdi-package-variant">
        {{ totalAssets }}
      </v-chip>
    </div>
    <div v-if="hasChildren && expanded">
      <LocationTreeItem
        v-for="child in node.children"
        :key="child.id"
        :node="child"
        :depth="(depth ?? 0) + 1"
      />
    </div>
  </div>
</template>

<style scoped>
.location-tree-row { min-height: 48px; border-radius: 8px; }
.location-tree-row:hover { background: rgba(var(--v-theme-primary), .06); }
.tree-spacer { display: inline-block; width: 28px; flex: 0 0 28px; }
.tree-link { min-width: 0; text-transform: none; letter-spacing: normal; }
</style>
