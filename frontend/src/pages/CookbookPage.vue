<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { recipeApi } from '../services/recipeApi'
import type { Ingredient, Recipe, RecipeWrite } from '../types/recipe'

const recipes = ref<Recipe[]>([]), search = ref(''), dialog = ref(false), error = ref(''), saving = ref(false)
const selected = ref<Recipe | null>(null), portions = ref(4)
const blank = (): RecipeWrite => ({ title: '', category: '', tags: [], preparation_minutes: null, cooking_minutes: null,
  servings: 4, favorite: false, image_url: null, ingredients: [{ amount: null, unit: '', name: '', note: '' }],
  steps: [''], notes: '', source_url: null, attachments: [] })
const form = ref<RecipeWrite>(blank())
const shownIngredients = computed(() => selected.value?.ingredients.map(item => ({ ...item,
  amount: item.amount === null ? null : item.amount * portions.value / selected.value!.servings })) ?? [])
async function load() { try { recipes.value = await recipeApi.list(search.value) } catch (e) { error.value = String(e) } }
function edit(recipe?: Recipe) { selected.value = recipe ?? null; form.value = recipe ? JSON.parse(JSON.stringify(recipe)) : blank(); portions.value = recipe?.servings ?? 4; dialog.value = true }
function addIngredient() { form.value.ingredients.push({ amount: null, unit: '', name: '', note: '' }) }
async function save() { saving.value = true; try { selected.value ? await recipeApi.update(selected.value.id, form.value) : await recipeApi.create(form.value); dialog.value = false; await load() } catch (e) { error.value = String(e) } finally { saving.value = false } }
async function duplicate(recipe: Recipe) { await recipeApi.duplicate(recipe.id); await load() }
async function remove(recipe: Recipe) { if (confirm(`„${recipe.title}“ wirklich löschen?`)) { await recipeApi.remove(recipe.id); await load() } }
function printRecipe(recipe: Recipe) { selected.value = recipe; portions.value = recipe.servings; setTimeout(() => window.print()) }
onMounted(load)
</script>

<template><v-container class="cookbook py-6">
  <div class="d-flex flex-wrap align-center ga-3 mb-5"><div><h1>Kochbuch</h1><p class="text-medium-emphasis">Strukturierte Rezepte im Wiki</p></div><v-spacer />
    <v-text-field v-model="search" label="Rezept oder Zutat suchen" prepend-inner-icon="mdi-magnify" hide-details max-width="360" @keyup.enter="load" />
    <v-btn color="primary" prepend-icon="mdi-plus" @click="edit()">Rezept anlegen</v-btn></div>
  <v-alert v-if="error" type="error" closable class="mb-4" @click:close="error=''">{{ error }}</v-alert>
  <v-row><v-col v-for="recipe in recipes" :key="recipe.id" cols="12" md="6" lg="4"><v-card height="100%">
    <v-img v-if="recipe.image_url" :src="recipe.image_url" height="180" cover /><v-card-title>{{ recipe.favorite ? '★ ' : '' }}{{ recipe.title }}</v-card-title>
    <v-card-subtitle>{{ recipe.category || 'Ohne Kategorie' }} · {{ recipe.servings }} Portionen</v-card-subtitle>
    <v-card-text><v-chip v-for="tag in recipe.tags" :key="tag" size="small" class="mr-1">{{ tag }}</v-chip><div class="mt-3">Vorbereitung {{ recipe.preparation_minutes ?? 0 }} Min. · Zubereitung {{ recipe.cooking_minutes ?? 0 }} Min.</div></v-card-text>
    <v-card-actions><v-btn @click="edit(recipe)">Öffnen</v-btn><v-btn icon="mdi-content-copy" title="Duplizieren" @click="duplicate(recipe)" /><v-btn icon="mdi-printer" title="Drucken" @click="printRecipe(recipe)" /><v-btn icon="mdi-delete-outline" color="error" title="Löschen" @click="remove(recipe)" /></v-card-actions>
  </v-card></v-col></v-row><v-empty-state v-if="!recipes.length" icon="mdi-chef-hat" title="Noch keine Rezepte" text="Lege dein erstes strukturiertes Rezept an." />

  <v-dialog v-model="dialog" max-width="1000" scrollable><v-card><v-card-title>{{ selected ? 'Rezept bearbeiten' : 'Rezept anlegen' }}</v-card-title><v-card-text>
    <v-row><v-col cols="12" md="8"><v-text-field v-model="form.title" label="Titel" /></v-col><v-col><v-checkbox v-model="form.favorite" label="Favorit" /></v-col>
    <v-col cols="12" md="6"><v-text-field v-model="form.category" label="Kategorie" /></v-col><v-col cols="12" md="6"><v-combobox v-model="form.tags" label="Tags" multiple chips /></v-col>
    <v-col cols="4"><v-text-field v-model.number="form.preparation_minutes" type="number" label="Vorbereitung (Min.)" /></v-col><v-col cols="4"><v-text-field v-model.number="form.cooking_minutes" type="number" label="Zubereitung (Min.)" /></v-col><v-col cols="4"><v-text-field v-model.number="form.servings" type="number" label="Portionen" /></v-col>
    <v-col cols="12"><v-text-field v-model="form.image_url" label="Bild-URL (optional)" /></v-col></v-row>
    <h3 class="mb-2">Zutaten</h3><v-row v-for="(item, i) in form.ingredients" :key="i" dense><v-col cols="3" md="2"><v-text-field v-model.number="item.amount" type="number" label="Menge" /></v-col><v-col cols="3" md="2"><v-text-field v-model="item.unit" label="Einheit" /></v-col><v-col><v-text-field v-model="item.name" label="Zutat" /></v-col><v-col cols="12" md="3"><v-text-field v-model="item.note" label="Hinweis" /></v-col></v-row><v-btn variant="tonal" @click="addIngredient">Zutat hinzufügen</v-btn>
    <h3 class="mt-5 mb-2">Zubereitung</h3><v-text-field v-for="(_, i) in form.steps" :key="i" v-model="form.steps[i]" :label="`Schritt ${i+1}`" prepend-inner-icon="mdi-numeric" /><v-btn variant="tonal" @click="form.steps.push('')">Schritt hinzufügen</v-btn>
    <v-textarea v-model="form.notes" label="Notizen" class="mt-5" /><v-text-field v-model="form.source_url" label="Quelle / URL (optional)" /><v-combobox v-model="form.attachments" label="Bilder / Anhänge (URLs)" multiple chips />
  </v-card-text><v-card-actions><v-spacer /><v-btn @click="dialog=false">Abbrechen</v-btn><v-btn color="primary" :loading="saving" :disabled="!form.title.trim()" @click="save">Speichern</v-btn></v-card-actions></v-card></v-dialog>

  <section v-if="selected" class="print-recipe"><h1>{{ selected.title }}</h1><p>{{ portions }} Portionen</p><label>Portionen <input v-model.number="portions" type="number" min="0.1" step="0.5"></label><h2>Zutaten</h2><ul><li v-for="(item,i) in shownIngredients" :key="i">{{ item.amount ?? '' }} {{ item.unit }} {{ item.name }} {{ item.note }}</li></ul><h2>Zubereitung</h2><ol><li v-for="step in selected.steps" :key="step">{{ step }}</li></ol><p>{{ selected.notes }}</p></section>
</v-container></template>
<style scoped>.print-recipe{display:none}@media print{.cookbook>*{display:none!important}.cookbook .print-recipe{display:block!important}.print-recipe input{border:0}}</style>
