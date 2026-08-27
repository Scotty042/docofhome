<script setup lang="ts">
import { ref } from 'vue'
import type { Recipe, RecipeWrite } from '../types/recipe'

const open = defineModel<boolean>('open', { required: true })
const form = defineModel<RecipeWrite>('form', { required: true })

const props = defineProps<{
  recipe: Recipe | null
  saving: boolean
  ingredientSuggestions: string[]
  unitSuggestions: string[]
  categorySuggestions: string[]
}>()

const emit = defineEmits<{
  (event: 'save'): void
}>()

const ingredientDragIndex = ref<number | null>(null)

function addIngredient() {
  form.value.ingredients.push({ amount: null, unit: '', name: '', note: '' })
}

function removeIngredient(index: number) {
  form.value.ingredients.splice(index, 1)
  if (!form.value.ingredients.length) addIngredient()
}

function moveIngredient(index: number, delta: number) {
  const target = index + delta
  if (target < 0 || target >= form.value.ingredients.length) return
  const [item] = form.value.ingredients.splice(index, 1)
  form.value.ingredients.splice(target, 0, item)
}

function beginIngredientDrag(index: number) {
  ingredientDragIndex.value = index
}

function dropIngredient(targetIndex: number) {
  const sourceIndex = ingredientDragIndex.value
  ingredientDragIndex.value = null
  if (sourceIndex === null || sourceIndex === targetIndex) return
  const [item] = form.value.ingredients.splice(sourceIndex, 1)
  form.value.ingredients.splice(targetIndex, 0, item)
}

function addStep() {
  form.value.steps.push('')
}

function removeStep(index: number) {
  form.value.steps.splice(index, 1)
  if (!form.value.steps.length) addStep()
}

function moveStep(index: number, delta: number) {
  const target = index + delta
  if (target < 0 || target >= form.value.steps.length) return
  const [step] = form.value.steps.splice(index, 1)
  form.value.steps.splice(target, 0, step)
}
</script>

<template>
  <v-dialog v-model="open" max-width="1360" width="calc(100vw - 24px)" scrollable persistent>
    <v-card class="recipe-editor-card" rounded="xl">
      <v-toolbar color="surface" flat>
        <v-toolbar-title class="font-weight-bold">{{ props.recipe ? 'Rezept bearbeiten' : 'Rezept anlegen' }}</v-toolbar-title>
        <v-btn icon="mdi-close" aria-label="Editor schließen" title="Schließen" @click="open = false" />
      </v-toolbar>

      <v-card-text class="recipe-editor-body">
        <section class="editor-section">
          <div class="editor-section-title"><v-icon color="primary">mdi-card-text-outline</v-icon><div><h2>Rezept</h2><p>Grunddaten und Darstellung</p></div></div>
          <v-row>
            <v-col cols="12" md="8"><v-text-field v-model="form.title" label="Titel" autofocus /></v-col>
            <v-col cols="12" sm="6" md="4"><v-checkbox v-model="form.favorite" label="Als Favorit markieren" hide-details /></v-col>
            <v-col cols="12" md="6"><v-combobox v-model="form.category" :items="categorySuggestions" label="Kategorie" clearable /></v-col>
            <v-col cols="12" md="6"><v-combobox v-model="form.tags" label="Tags" multiple chips closable-chips /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model.number="form.preparation_minutes" type="number" min="0" label="Vorbereitung (Min.)" /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model.number="form.cooking_minutes" type="number" min="0" label="Zubereitung (Min.)" /></v-col>
            <v-col cols="12" sm="4"><v-text-field v-model.number="form.servings" type="number" min="0.1" step="0.5" label="Portionen" /></v-col>
            <v-col cols="12"><v-text-field v-model="form.image_url" label="Bild-URL (optional)" prepend-inner-icon="mdi-image-outline" /></v-col>
          </v-row>
        </section>

        <v-divider class="my-6" />

        <section class="editor-section">
          <div class="editor-section-title ingredients-title">
            <div class="d-flex align-center ga-3"><v-icon color="primary">mdi-food-variant</v-icon><div><h2>Zutaten</h2><p>Menge, Einheit und Zutat direkt in einer Zeile erfassen</p></div></div>
            <v-btn color="primary" prepend-icon="mdi-plus" variant="tonal" @click="addIngredient">Zutat hinzufügen</v-btn>
          </div>

          <div class="ingredient-editor-list">
            <div
              v-for="(item, index) in form.ingredients"
              :key="index"
              class="ingredient-editor-row"
              @dragover.prevent
              @drop="dropIngredient(index)"
            >
              <v-icon
                class="ingredient-drag"
                draggable="true"
                title="Zutat verschieben"
                @dragstart="beginIngredientDrag(index)"
              >mdi-drag-vertical</v-icon>
              <v-text-field v-model.number="item.amount" class="ingredient-amount" type="number" min="0" step="any" label="Menge" hide-details="auto" />
              <v-combobox v-model="item.unit" class="ingredient-unit" :items="unitSuggestions" label="Einheit" clearable hide-details="auto" />
              <v-combobox v-model="item.name" class="ingredient-name" :items="ingredientSuggestions" label="Zutat" clearable hide-details="auto" />
              <v-text-field v-model="item.note" class="ingredient-note" label="Notiz" hide-details="auto" />
              <v-menu>
                <template #activator="{ props: menuProps }"><v-btn v-bind="menuProps" class="ingredient-actions" icon="mdi-dots-vertical" variant="text" title="Zutatenaktionen" /></template>
                <v-list density="compact">
                  <v-list-item prepend-icon="mdi-arrow-up" title="Nach oben" :disabled="index === 0" @click="moveIngredient(index, -1)" />
                  <v-list-item prepend-icon="mdi-arrow-down" title="Nach unten" :disabled="index === form.ingredients.length - 1" @click="moveIngredient(index, 1)" />
                  <v-divider />
                  <v-list-item prepend-icon="mdi-delete-outline" title="Löschen" base-color="error" @click="removeIngredient(index)" />
                </v-list>
              </v-menu>
            </div>
          </div>
          <v-btn class="mt-3" prepend-icon="mdi-plus" variant="text" @click="addIngredient">Weitere Zutat</v-btn>
        </section>

        <v-divider class="my-6" />

        <section class="editor-section">
          <div class="editor-section-title ingredients-title">
            <div class="d-flex align-center ga-3"><v-icon color="primary">mdi-format-list-numbered</v-icon><div><h2>Zubereitung</h2><p>Ein Arbeitsschritt pro Karte</p></div></div>
            <v-btn color="primary" prepend-icon="mdi-plus" variant="tonal" @click="addStep">Schritt hinzufügen</v-btn>
          </div>

          <div class="step-editor-list">
            <v-card v-for="(_, index) in form.steps" :key="index" class="step-editor-card" variant="outlined">
              <v-card-text>
                <div class="step-editor-number">{{ index + 1 }}</div>
                <v-textarea v-model="form.steps[index]" :label="`Schritt ${index + 1}`" auto-grow rows="2" hide-details="auto" />
                <v-menu>
                  <template #activator="{ props: menuProps }"><v-btn v-bind="menuProps" icon="mdi-dots-vertical" variant="text" title="Schrittaktionen" /></template>
                  <v-list density="compact">
                    <v-list-item prepend-icon="mdi-arrow-up" title="Nach oben" :disabled="index === 0" @click="moveStep(index, -1)" />
                    <v-list-item prepend-icon="mdi-arrow-down" title="Nach unten" :disabled="index === form.steps.length - 1" @click="moveStep(index, 1)" />
                    <v-divider />
                    <v-list-item prepend-icon="mdi-delete-outline" title="Löschen" base-color="error" @click="removeStep(index)" />
                  </v-list>
                </v-menu>
              </v-card-text>
            </v-card>
          </div>
          <v-btn class="mt-3" prepend-icon="mdi-plus" variant="text" @click="addStep">Weiterer Schritt</v-btn>
        </section>

        <v-divider class="my-6" />

        <section class="editor-section">
          <div class="editor-section-title"><v-icon color="primary">mdi-note-text-outline</v-icon><div><h2>Weitere Angaben</h2><p>Notizen, Quelle und Anhänge</p></div></div>
          <v-textarea v-model="form.notes" label="Notizen" auto-grow rows="3" />
          <v-text-field v-model="form.source_url" label="Quelle / URL (optional)" prepend-inner-icon="mdi-link-variant" />
          <v-combobox v-model="form.attachments" label="Bilder / Anhänge (URLs)" multiple chips closable-chips prepend-inner-icon="mdi-paperclip" />
        </section>
      </v-card-text>

      <v-divider />
      <v-card-actions class="editor-actions pa-4">
        <v-spacer />
        <v-btn @click="open = false">Abbrechen</v-btn>
        <v-btn color="primary" prepend-icon="mdi-content-save" :loading="saving" :disabled="!form.title.trim()" @click="emit('save')">Speichern</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.recipe-editor-card { max-height: calc(100dvh - 24px); }
.recipe-editor-body { padding: 24px; overflow-y: auto; -webkit-overflow-scrolling: touch; }
.editor-section-title { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.editor-section-title h2 { margin: 0; font-size: 1.25rem; }
.editor-section-title p { margin: 2px 0 0; color: rgba(var(--v-theme-on-surface), .58); font-size: .84rem; }
.ingredients-title { justify-content: space-between; }
.ingredient-editor-list, .step-editor-list { display: grid; gap: 10px; }
.ingredient-editor-row {
  display: grid;
  grid-template-columns: 34px 110px 150px minmax(210px, 1.35fr) minmax(170px, .95fr) 44px;
  grid-template-areas: "drag amount unit ingredient note actions";
  gap: 10px;
  align-items: start;
  padding: 10px;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 14px;
  background: rgba(var(--v-theme-surface), .55);
}
.ingredient-drag { grid-area: drag; align-self: center; margin-top: 10px; cursor: grab; color: rgba(var(--v-theme-on-surface), .5); touch-action: none; }
.ingredient-amount { grid-area: amount; }
.ingredient-unit { grid-area: unit; }
.ingredient-name { grid-area: ingredient; }
.ingredient-note { grid-area: note; }
.ingredient-actions { grid-area: actions; }
.step-editor-card { border-radius: 14px; }
.step-editor-card .v-card-text { display: grid; grid-template-columns: 42px minmax(0, 1fr) 44px; gap: 12px; align-items: start; padding: 14px; }
.step-editor-number { display: grid; place-items: center; width: 38px; height: 38px; margin-top: 3px; border-radius: 11px; background: rgba(var(--v-theme-primary), .13); color: rgb(var(--v-theme-primary)); font-weight: 800; }
.editor-actions { position: sticky; bottom: 0; background: rgb(var(--v-theme-surface)); }

@media (max-width: 1050px) {
  .ingredient-editor-row {
    grid-template-columns: 34px 105px minmax(120px, 1fr) 44px;
    grid-template-areas:
      "drag amount unit actions"
      "drag ingredient ingredient actions"
      ". note note .";
  }
}

@media (max-width: 600px) {
  .recipe-editor-body { padding: 16px; }
  .ingredients-title { align-items: flex-start; flex-direction: column; }
  .ingredient-editor-row { gap: 8px; padding: 8px; }
  .step-editor-card .v-card-text { grid-template-columns: 34px minmax(0, 1fr) 36px; gap: 8px; padding: 10px; }
  .step-editor-number { width: 32px; height: 32px; }
  .editor-actions .v-btn { min-height: 44px; }
}
</style>
