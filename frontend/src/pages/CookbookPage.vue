<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import RecipeCookMode from '../components/RecipeCookMode.vue'
import RecipeDetailDialog from '../components/RecipeDetailDialog.vue'
import RecipeEditorDialog from '../components/RecipeEditorDialog.vue'
import { recipeApi } from '../services/recipeApi'
import type { Recipe, RecipeWrite } from '../types/recipe'

const recipes = ref<Recipe[]>([])
const search = ref('')
const detailDialog = ref(false)
const editorDialog = ref(false)
const cookMode = ref(false)
const error = ref('')
const saving = ref(false)
const selected = ref<Recipe | null>(null)
const printSelection = ref<Recipe | null>(null)
const portions = ref(4)
let previousBodyOverflow = ''

const blank = (): RecipeWrite => ({
  title: '',
  category: '',
  tags: [],
  preparation_minutes: null,
  cooking_minutes: null,
  servings: 4,
  favorite: false,
  image_url: null,
  ingredients: [{ amount: null, unit: '', name: '', note: '' }],
  steps: [''],
  notes: '',
  source_url: null,
  attachments: []
})

const form = ref<RecipeWrite>(blank())

const ingredientSuggestions = computed(() => uniqueSorted(
  recipes.value.flatMap((recipe) => recipe.ingredients.map((ingredient) => ingredient.name))
))
const categorySuggestions = computed(() => uniqueSorted(recipes.value.map((recipe) => recipe.category)))
const unitSuggestions = computed(() => uniqueSorted([
  'g', 'kg', 'ml', 'l', 'dl', 'EL', 'TL', 'Stk.', 'Pkg.', 'Prise', 'Dose', 'Bund',
  ...recipes.value.flatMap((recipe) => recipe.ingredients.map((ingredient) => ingredient.unit))
]))

const printIngredients = computed(() => {
  const recipe = printSelection.value
  if (!recipe) return []
  const servings = recipe.servings > 0 ? recipe.servings : 1
  return recipe.ingredients.map((ingredient) => ({
    ...ingredient,
    amount: ingredient.amount === null ? null : ingredient.amount * portions.value / servings
  }))
})

function uniqueSorted(values: string[]) {
  return [...new Set(values.map((value) => value.trim()).filter(Boolean))]
    .sort((left, right) => left.localeCompare(right, 'de', { sensitivity: 'base' }))
}

function recipeToWrite(recipe: Recipe): RecipeWrite {
  return {
    title: recipe.title,
    category: recipe.category,
    tags: [...recipe.tags],
    preparation_minutes: recipe.preparation_minutes,
    cooking_minutes: recipe.cooking_minutes,
    servings: recipe.servings,
    favorite: recipe.favorite,
    image_url: recipe.image_url,
    ingredients: recipe.ingredients.map((ingredient) => ({ ...ingredient })),
    steps: [...recipe.steps],
    notes: recipe.notes,
    source_url: recipe.source_url,
    attachments: [...recipe.attachments]
  }
}

function optionalNumber(value: unknown): number | null {
  if (value === null || value === undefined || value === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

function normalizeUrl(value: string | null) {
  const normalized = String(value ?? '').trim()
  return normalized || null
}

function normalizedForm(): RecipeWrite {
  const data = form.value
  return {
    title: data.title.trim(),
    category: data.category.trim(),
    tags: uniqueSorted(data.tags),
    preparation_minutes: optionalNumber(data.preparation_minutes),
    cooking_minutes: optionalNumber(data.cooking_minutes),
    servings: Number(data.servings),
    favorite: data.favorite,
    image_url: normalizeUrl(data.image_url),
    ingredients: data.ingredients
      .map((ingredient) => ({
        amount: optionalNumber(ingredient.amount),
        unit: ingredient.unit.trim(),
        name: ingredient.name.trim(),
        note: ingredient.note.trim()
      }))
      .filter((ingredient) => ingredient.name),
    steps: data.steps.map((step) => step.trim()).filter(Boolean),
    notes: data.notes.trim(),
    source_url: normalizeUrl(data.source_url),
    attachments: uniqueSorted(data.attachments),
  }
}

function formatAmount(value: number | null) {
  if (value === null) return ''
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(value)
}

async function load() {
  try {
    recipes.value = await recipeApi.list(search.value)
    error.value = ''
  } catch (exception) {
    error.value = String(exception)
  }
}

function openRecipe(recipe: Recipe) {
  selected.value = recipe
  portions.value = recipe.servings
  detailDialog.value = true
}

function edit(recipe?: Recipe) {
  const target = recipe ?? selected.value
  if (recipe) selected.value = recipe
  form.value = target ? recipeToWrite(target) : blank()
  editorDialog.value = true
}

async function save() {
  const payload = normalizedForm()
  if (!payload.title) return
  if (!Number.isFinite(payload.servings) || payload.servings <= 0) {
    error.value = 'Bitte eine gültige Portionszahl größer als 0 angeben.'
    return
  }

  saving.value = true
  try {
    const saved = selected.value
      ? await recipeApi.update(selected.value.id, payload)
      : await recipeApi.create(payload)
    editorDialog.value = false
    selected.value = saved
    portions.value = saved.servings
    detailDialog.value = true
    await load()
  } catch (exception) {
    error.value = String(exception)
  } finally {
    saving.value = false
  }
}

async function duplicate(recipe: Recipe) {
  try {
    const copy = await recipeApi.duplicate(recipe.id)
    await load()
    openRecipe(copy)
  } catch (exception) {
    error.value = String(exception)
  }
}

async function remove(recipe: Recipe) {
  if (!confirm(`„${recipe.title}“ wirklich löschen?`)) return
  try {
    await recipeApi.remove(recipe.id)
    if (selected.value?.id === recipe.id) {
      detailDialog.value = false
      selected.value = null
    }
    await load()
  } catch (exception) {
    error.value = String(exception)
  }
}

function printRecipe(recipe: Recipe) {
  printSelection.value = recipe
  portions.value = recipe.servings
  setTimeout(() => window.print())
}

async function startCookMode() {
  if (!selected.value) return
  portions.value = portions.value || selected.value.servings
  previousBodyOverflow = document.body.style.overflow
  document.body.style.overflow = 'hidden'
  cookMode.value = true

  const requestFullscreen = document.documentElement.requestFullscreen?.bind(document.documentElement)
  if (requestFullscreen && !document.fullscreenElement) {
    try { await requestFullscreen() } catch { /* Die viewportfüllende Kochansicht bleibt als Fallback aktiv. */ }
  }
}

async function closeCookMode() {
  cookMode.value = false
  document.body.style.overflow = previousBodyOverflow
  if (document.fullscreenElement && document.exitFullscreen) {
    try { await document.exitFullscreen() } catch { /* Der Browser kann Vollbild auch selbst beenden. */ }
  }
}

function editSelected() {
  if (!selected.value) return
  edit(selected.value)
}

onMounted(load)
onBeforeUnmount(() => {
  document.body.style.overflow = previousBodyOverflow
  if (document.fullscreenElement && document.exitFullscreen) void document.exitFullscreen().catch(() => undefined)
})
</script>

<template>
  <v-container class="cookbook py-6" fluid>
    <div class="cookbook-header d-flex flex-wrap align-center ga-3 mb-5">
      <div>
        <h1>Kochbuch</h1>
        <p class="text-medium-emphasis">Strukturierte Rezepte im Wiki</p>
      </div>
      <v-spacer />
      <v-text-field
        v-model="search"
        class="cookbook-search"
        label="Rezept oder Zutat suchen"
        prepend-inner-icon="mdi-magnify"
        hide-details
        clearable
        @keyup.enter="load"
        @click:clear="search = ''; load()"
      />
      <v-btn color="primary" prepend-icon="mdi-plus" @click="selected = null; edit()">Rezept anlegen</v-btn>
    </div>

    <v-alert v-if="error" type="error" closable class="mb-4" @click:close="error = ''">{{ error }}</v-alert>

    <v-row>
      <v-col v-for="recipe in recipes" :key="recipe.id" cols="12" sm="6" lg="4" xl="3">
        <v-card class="recipe-card" height="100%" rounded="lg" @click="openRecipe(recipe)">
          <div class="recipe-image-wrap">
            <v-img v-if="recipe.image_url" :src="recipe.image_url" height="210" cover />
            <div v-else class="recipe-image-placeholder"><v-icon size="64">mdi-food</v-icon></div>
            <v-chip v-if="recipe.favorite" class="favorite-chip" color="warning" size="small" prepend-icon="mdi-star">Favorit</v-chip>
          </div>
          <v-card-title class="recipe-card-title">{{ recipe.title }}</v-card-title>
          <v-card-subtitle>{{ recipe.category || 'Ohne Kategorie' }} · {{ recipe.servings }} Portionen</v-card-subtitle>
          <v-card-text>
            <div class="recipe-card-meta">
              <span><v-icon size="18">mdi-clock-start</v-icon>{{ recipe.preparation_minutes ?? 0 }} Min.</span>
              <span><v-icon size="18">mdi-stove</v-icon>{{ recipe.cooking_minutes ?? 0 }} Min.</span>
            </div>
            <div v-if="recipe.tags.length" class="mt-3">
              <v-chip v-for="tag in recipe.tags.slice(0, 4)" :key="tag" size="small" class="mr-1 mb-1" variant="tonal">{{ tag }}</v-chip>
            </div>
          </v-card-text>
          <v-card-actions @click.stop>
            <v-btn color="primary" variant="text" prepend-icon="mdi-book-open-variant" @click="openRecipe(recipe)">Öffnen</v-btn>
            <v-spacer />
            <v-menu>
              <template #activator="{ props: menuProps }"><v-btn v-bind="menuProps" icon="mdi-dots-vertical" variant="text" title="Rezeptaktionen" /></template>
              <v-list density="compact">
                <v-list-item prepend-icon="mdi-pencil" title="Bearbeiten" @click="edit(recipe)" />
                <v-list-item prepend-icon="mdi-content-copy" title="Duplizieren" @click="duplicate(recipe)" />
                <v-list-item prepend-icon="mdi-printer" title="Drucken" @click="printRecipe(recipe)" />
                <v-divider />
                <v-list-item prepend-icon="mdi-delete-outline" title="Löschen" base-color="error" @click="remove(recipe)" />
              </v-list>
            </v-menu>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-empty-state
      v-if="!recipes.length"
      icon="mdi-chef-hat"
      title="Noch keine Rezepte"
      text="Lege dein erstes strukturiertes Rezept an."
    />

    <RecipeDetailDialog
      v-model="detailDialog"
      :recipe="selected"
      :portions="portions"
      @update:portions="portions = $event"
      @edit="editSelected"
      @cook="startCookMode"
      @print="selected && printRecipe(selected)"
    />

    <RecipeEditorDialog
      v-model:open="editorDialog"
      v-model:form="form"
      :recipe="selected"
      :saving="saving"
      :ingredient-suggestions="ingredientSuggestions"
      :unit-suggestions="unitSuggestions"
      :category-suggestions="categorySuggestions"
      @save="save"
    />

    <RecipeCookMode
      v-if="cookMode && selected"
      :recipe="selected"
      :portions="portions"
      @update:portions="portions = $event"
      @close="closeCookMode"
    />

    <section v-if="printSelection" class="print-recipe">
      <h1>{{ printSelection.title }}</h1>
      <p>{{ portions }} Portionen</p>
      <h2>Zutaten</h2>
      <ul>
        <li v-for="(item, index) in printIngredients" :key="index">
          <strong v-if="item.amount !== null || item.unit" class="print-ingredient-quantity">{{ formatAmount(item.amount) }}{{ item.amount !== null && item.unit ? ' ' : '' }}{{ item.unit }}</strong>{{ item.name }}<span v-if="item.note"> – {{ item.note }}</span>
        </li>
      </ul>
      <h2>Zubereitung</h2>
      <ol><li v-for="(step, index) in printSelection.steps" :key="index">{{ step }}</li></ol>
      <p v-if="printSelection.notes" class="print-notes">{{ printSelection.notes }}</p>
    </section>
  </v-container>
</template>

<style scoped>
.cookbook { max-width: 1680px; }
.cookbook-header h1 { line-height: 1.1; }
.cookbook-header p { margin: 4px 0 0; }
.cookbook-search { flex: 0 1 380px; min-width: min(300px, 100%); }
.recipe-card { cursor: pointer; overflow: hidden; transition: transform .16s ease, box-shadow .16s ease; }
.recipe-card:hover { transform: translateY(-2px); box-shadow: 0 7px 22px rgba(0, 0, 0, .12); }
.recipe-image-wrap { position: relative; }
.recipe-image-placeholder { display: grid; place-items: center; height: 210px; color: rgba(var(--v-theme-on-surface), .18); background: rgba(var(--v-theme-primary), .05); }
.favorite-chip { position: absolute; top: 12px; right: 12px; }
.recipe-card-title { white-space: normal; line-height: 1.25; }
.recipe-card-meta { display: flex; flex-wrap: wrap; gap: 16px; color: rgba(var(--v-theme-on-surface), .68); }
.recipe-card-meta span { display: flex; align-items: center; gap: 6px; }
.print-recipe { display: none; }
.print-notes { margin-top: 22px; white-space: pre-wrap; }
.print-ingredient-quantity { margin-right: .35em; }

@media (max-width: 600px) {
  .cookbook { padding-left: 12px !important; padding-right: 12px !important; }
  .cookbook-search { flex-basis: 100%; }
  .cookbook-header > .v-btn { width: 100%; min-height: 44px; }
  .recipe-card .v-card-actions { min-height: 52px; }
}

@media print {
  :global(.v-overlay-container),
  :global(.v-app-bar),
  :global(.v-navigation-drawer) { display: none !important; }
  .cookbook > *:not(.print-recipe) { display: none !important; }
  .cookbook .print-recipe { display: block !important; color: #000; background: #fff; }
  .print-recipe li { margin-bottom: 6px; }
}
</style>
