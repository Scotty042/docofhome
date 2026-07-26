<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { locationApi } from '../services/locationApi'
import type { LocationTreeNode, LocationType, LocationWrite } from '../types/locations'

type EditableEntry = {
  id: string | null
  name: string
  original: LocationTreeNode | null
}

type EditableFloor = EditableEntry & { rooms: EditableEntry[] }

const loading = ref(true)
const saving = ref(false)
const error = ref<string | null>(null)
const success = ref<string | null>(null)
const tree = ref<LocationTreeNode[]>([])
const buildings = ref<LocationTreeNode[]>([])
const selectedBuildingId = ref<string | null>(null)
const buildingName = ref('Zuhause')
const buildingOriginal = ref<LocationTreeNode | null>(null)
const floorCount = ref(1)
const floors = ref<EditableFloor[]>([])
const hasOutdoor = ref(false)
const outdoorAreas = ref<EditableEntry[]>([])

const existingFloorCount = computed(() => floors.value.filter((item) => item.id).length)
const canSave = computed(() => {
  if (!buildingName.value.trim()) return false
  if (!floors.value.length) return false
  return floors.value.every((floor) => floor.name.trim() && floor.rooms.every((room) => room.name.trim()))
    && (!hasOutdoor.value || (outdoorAreas.value.length > 0 && outdoorAreas.value.every((area) => area.name.trim())))
})

function entry(node?: LocationTreeNode | null, fallback = ''): EditableEntry {
  return { id: node?.id ?? null, name: node?.name ?? fallback, original: node ?? null }
}

function floorEntry(node?: LocationTreeNode | null, index = 0): EditableFloor {
  return {
    ...entry(node, index === 0 ? 'Erdgeschoss' : `Etage ${index + 1}`),
    rooms: (node?.children ?? [])
      .filter((child) => child.location_type === 'room')
      .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
      .map((room) => entry(room))
  }
}

function applyBuilding(node: LocationTreeNode | null) {
  buildingOriginal.value = node
  buildingName.value = node?.name ?? 'Zuhause'
  const floorNodes = (node?.children ?? [])
    .filter((child) => child.location_type === 'floor')
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
  floors.value = floorNodes.length
    ? floorNodes.map((floor, index) => floorEntry(floor, index))
    : [floorEntry(null, 0)]
  floorCount.value = floors.value.length
  outdoorAreas.value = (node?.children ?? [])
    .filter((child) => child.location_type === 'outdoor')
    .sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
    .map((area) => entry(area))
  hasOutdoor.value = outdoorAreas.value.length > 0
  error.value = null
}

function updateFloorCount(value: string | number | null) {
  const requested = Math.max(1, Math.min(20, Number(value) || 1))
  const minimum = existingFloorCount.value || 1
  const count = Math.max(requested, minimum)
  floorCount.value = count
  while (floors.value.length < count) floors.value.push(floorEntry(null, floors.value.length))
  while (floors.value.length > count && !floors.value.at(-1)?.id) floors.value.pop()
  floorCount.value = floors.value.length
  if (requested < minimum) {
    error.value = 'Bereits vorhandene Etagen werden im Assistenten nicht gelöscht. Archiviere sie bei Bedarf in der jeweiligen Detailansicht.'
  }
}

function addRoom(floor: EditableFloor) {
  floor.rooms.push(entry(null, `Raum ${floor.rooms.length + 1}`))
}

function removeRoom(floor: EditableFloor, index: number) {
  if (floor.rooms[index]?.id) {
    error.value = 'Bereits vorhandene Räume werden hier nicht gelöscht. Du kannst sie umbenennen oder in der Raumansicht archivieren.'
    return
  }
  floor.rooms.splice(index, 1)
}

function addOutdoorArea() {
  hasOutdoor.value = true
  outdoorAreas.value.push(entry(null, outdoorAreas.value.length ? `Außenbereich ${outdoorAreas.value.length + 1}` : 'Garten'))
}

function removeOutdoorArea(index: number) {
  if (outdoorAreas.value[index]?.id) {
    error.value = 'Bereits vorhandene Außenbereiche werden hier nicht gelöscht. Du kannst sie umbenennen oder in der Detailansicht archivieren.'
    return
  }
  outdoorAreas.value.splice(index, 1)
  if (!outdoorAreas.value.length) hasOutdoor.value = false
}

function locationPayload(
  item: EditableEntry,
  locationType: LocationType,
  parentId: string | null,
  sortOrder: number
): LocationWrite {
  return {
    name: item.name.trim(),
    location_type: locationType,
    parent_id: parentId,
    description: item.original?.description ?? null,
    short_name: item.original?.short_name ?? null,
    sort_order: sortOrder,
    notes: item.original?.notes ?? null
  }
}

function duplicateNames(values: EditableEntry[]) {
  const seen = new Set<string>()
  for (const value of values) {
    const normalized = value.name.trim().toLocaleLowerCase('de-DE')
    if (!normalized || seen.has(normalized)) return true
    seen.add(normalized)
  }
  return false
}

async function save() {
  error.value = null
  success.value = null
  if (!canSave.value) {
    error.value = 'Bitte gib für Gebäude, Etagen und alle angelegten Räume einen Namen an.'
    return
  }
  if (duplicateNames(floors.value) || floors.value.some((floor) => duplicateNames(floor.rooms))) {
    error.value = 'Etagen und Räume dürfen innerhalb derselben Ebene nicht doppelt benannt sein.'
    return
  }
  if (hasOutdoor.value && duplicateNames(outdoorAreas.value)) {
    error.value = 'Außenbereiche dürfen nicht doppelt benannt sein.'
    return
  }

  saving.value = true
  try {
    let buildingId = selectedBuildingId.value
    if (buildingId && buildingOriginal.value) {
      await locationApi.update(buildingId, locationPayload(
        { id: buildingId, name: buildingName.value, original: buildingOriginal.value },
        'building', buildingOriginal.value.parent_id, buildingOriginal.value.sort_order ?? 0
      ))
    } else {
      const created = await locationApi.create({
        name: buildingName.value.trim(), location_type: 'building', parent_id: null,
        description: null, short_name: null, sort_order: 0, notes: null
      })
      buildingId = created.id
    }

    for (let floorIndex = 0; floorIndex < floors.value.length; floorIndex += 1) {
      const floor = floors.value[floorIndex]!
      const floorPayload = locationPayload(floor, 'floor', buildingId, floorIndex)
      const savedFloor = floor.id
        ? await locationApi.update(floor.id, floorPayload)
        : await locationApi.create(floorPayload)
      floor.id = savedFloor.id
      floor.original = savedFloor as LocationTreeNode
      for (let roomIndex = 0; roomIndex < floor.rooms.length; roomIndex += 1) {
        const room = floor.rooms[roomIndex]!
        const roomPayload = locationPayload(room, 'room', savedFloor.id, roomIndex)
        const savedRoom = room.id
          ? await locationApi.update(room.id, roomPayload)
          : await locationApi.create(roomPayload)
        room.id = savedRoom.id
        room.original = savedRoom as LocationTreeNode
      }
    }

    if (hasOutdoor.value) {
      for (let index = 0; index < outdoorAreas.value.length; index += 1) {
        const area = outdoorAreas.value[index]!
        const areaPayload = locationPayload(area, 'outdoor', buildingId, index)
        const savedArea = area.id
          ? await locationApi.update(area.id, areaPayload)
          : await locationApi.create(areaPayload)
        area.id = savedArea.id
        area.original = savedArea as LocationTreeNode
      }
    }

    selectedBuildingId.value = buildingId
    success.value = 'Gebäudestruktur gespeichert. Etagen und Räume wurden direkt korrekt zugeordnet.'
    await load()
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Gebäudestruktur konnte nicht gespeichert werden.'
  } finally {
    saving.value = false
  }
}

async function load() {
  loading.value = true
  try {
    tree.value = await locationApi.tree()
    buildings.value = tree.value.filter((item) => item.location_type === 'building')
    const requested = selectedBuildingId.value
      ? buildings.value.find((item) => item.id === selectedBuildingId.value) ?? null
      : buildings.value[0] ?? null
    selectedBuildingId.value = requested?.id ?? null
    applyBuilding(requested)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : 'Gebäudestruktur konnte nicht geladen werden.'
  } finally {
    loading.value = false
  }
}

watch(selectedBuildingId, (value) => {
  if (loading.value) return
  success.value = null
  applyBuilding(buildings.value.find((item) => item.id === value) ?? null)
})

watch(hasOutdoor, (enabled) => {
  if (loading.value || !enabled || outdoorAreas.value.length) return
  addOutdoorArea()
})

onMounted(load)
</script>

<template>
  <v-container fluid class="structure-wizard pa-4 pa-md-6">
    <div class="d-flex flex-wrap align-center ga-3 mb-5">
      <div>
        <h1>Gebäudestruktur einrichten</h1>
        <p class="text-medium-emphasis mb-0">
          Etagen, Räume und Außenbereiche geführt anlegen oder vorhandene Namen ergänzen.
        </p>
      </div>
      <v-spacer />
      <v-btn variant="text" prepend-icon="mdi-arrow-left" to="/locations">Zurück zu Bereiche & Räume</v-btn>
    </div>

    <v-alert v-if="error" type="error" variant="tonal" class="mb-4" closable @click:close="error = null">
      {{ error }}
    </v-alert>
    <v-alert v-if="success" type="success" variant="tonal" class="mb-4">
      {{ success }}
    </v-alert>
    <v-progress-linear v-if="loading" indeterminate class="mb-4" />

    <template v-if="!loading">
      <v-card title="1. Gebäude" prepend-icon="mdi-home-outline" class="mb-5">
        <v-card-text>
          <v-select
            v-if="buildings.length"
            v-model="selectedBuildingId"
            :items="buildings"
            item-title="name"
            item-value="id"
            label="Vorhandenes Gebäude"
            hint="Bei mehreren Gebäuden wählst du hier die zu bearbeitende Struktur."
            persistent-hint
            class="mb-3"
          />
          <v-alert v-else type="info" variant="tonal" class="mb-3">
            Es ist noch kein Gebäude vorhanden. Beim Speichern wird ein neues Gebäude angelegt.
          </v-alert>
          <v-text-field v-model="buildingName" label="Name des Gebäudes" maxlength="150" />
        </v-card-text>
      </v-card>

      <v-card title="2. Etagen und Räume" prepend-icon="mdi-home-floor-0" class="mb-5">
        <v-card-text>
          <v-text-field
            v-model.number="floorCount"
            type="number"
            min="1"
            max="20"
            label="Wie viele Etagen gibt es?"
            hint="Vorhandene Etagen werden nicht automatisch gelöscht."
            persistent-hint
            class="mb-4"
            @update:model-value="updateFloorCount"
          />

          <v-card v-for="(floor, floorIndex) in floors" :key="floor.id ?? `new-${floorIndex}`" variant="outlined" class="mb-4">
            <v-card-title class="d-flex align-center ga-2">
              <v-icon icon="mdi-home-floor-0" />
              <span>Etage {{ floorIndex + 1 }}</span>
              <v-chip v-if="floor.id" size="x-small" color="success" variant="tonal">vorhanden</v-chip>
            </v-card-title>
            <v-card-text>
              <v-text-field v-model="floor.name" label="Name der Etage" maxlength="150" />
              <div class="text-subtitle-2 mb-2">Räume auf dieser Etage</div>
              <div v-for="(room, roomIndex) in floor.rooms" :key="room.id ?? `room-${roomIndex}`" class="d-flex ga-2 align-start mb-2">
                <v-text-field v-model="room.name" :label="`Raum ${roomIndex + 1}`" hide-details />
                <v-btn
                  icon="mdi-delete-outline"
                  variant="text"
                  color="error"
                  :aria-label="`${room.name || 'Raum'} entfernen`"
                  @click="removeRoom(floor, roomIndex)"
                />
              </div>
              <v-btn variant="tonal" prepend-icon="mdi-plus" @click="addRoom(floor)">Raum hinzufügen</v-btn>
            </v-card-text>
          </v-card>
        </v-card-text>
      </v-card>

      <v-card title="3. Außenbereiche" prepend-icon="mdi-tree-outline" class="mb-5">
        <v-card-text>
          <v-switch v-model="hasOutdoor" label="Es gibt einen Außenbereich" color="primary" inset />
          <template v-if="hasOutdoor">
            <div v-for="(area, index) in outdoorAreas" :key="area.id ?? `outdoor-${index}`" class="d-flex ga-2 align-start mb-2">
              <v-text-field v-model="area.name" :label="`Außenbereich ${index + 1}`" hide-details />
              <v-btn icon="mdi-delete-outline" variant="text" color="error" @click="removeOutdoorArea(index)" />
            </div>
            <v-btn variant="tonal" prepend-icon="mdi-plus" @click="addOutdoorArea">Außenbereich hinzufügen</v-btn>
          </template>
        </v-card-text>
      </v-card>

      <div class="d-flex flex-wrap justify-end ga-3">
        <v-btn variant="text" to="/locations">Abbrechen</v-btn>
        <v-btn color="primary" prepend-icon="mdi-content-save" :loading="saving" :disabled="!canSave" @click="save">
          Gebäudestruktur speichern
        </v-btn>
      </div>
    </template>
  </v-container>
</template>

<style scoped>
.structure-wizard { max-width: 1100px; }
h1 { font-size: clamp(1.7rem, 5vw, 2.4rem); }
</style>
