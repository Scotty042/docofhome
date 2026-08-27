<script setup lang="ts">
import { computed } from 'vue'
import type { Recipe } from '../types/recipe'

const props = defineProps<{
  modelValue: boolean
  recipe: Recipe | null
  portions: number
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: boolean): void
  (event: 'update:portions', value: number): void
  (event: 'edit'): void
  (event: 'cook'): void
  (event: 'print'): void
}>()

const totalMinutes = computed(() => (props.recipe?.preparation_minutes ?? 0) + (props.recipe?.cooking_minutes ?? 0))
const scaledIngredients = computed(() => {
  if (!props.recipe) return []
  const servings = props.recipe.servings > 0 ? props.recipe.servings : 1
  return props.recipe.ingredients.map((ingredient) => ({
    ...ingredient,
    amount: ingredient.amount === null ? null : ingredient.amount * props.portions / servings
  }))
})

function formatAmount(value: number | null) {
  if (value === null) return ''
  return new Intl.NumberFormat('de-DE', { maximumFractionDigits: 2 }).format(value)
}

function adjustPortions(delta: number) {
  emit('update:portions', Math.max(1, props.portions + delta))
}
</script>

<template>
  <v-dialog
    :model-value="modelValue"
    max-width="1220"
    width="calc(100vw - 24px)"
    scrollable
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card v-if="recipe" class="recipe-detail-card" rounded="xl">
      <v-toolbar color="surface" flat>
        <v-toolbar-title class="font-weight-bold">{{ recipe.title }}</v-toolbar-title>
        <v-btn icon="mdi-close" aria-label="Rezept schließen" title="Schließen" @click="emit('update:modelValue', false)" />
      </v-toolbar>

      <v-card-text class="recipe-detail-body pa-0">
        <div class="recipe-hero">
          <div class="recipe-hero-copy">
            <div class="d-flex flex-wrap align-center ga-2 mb-3">
              <v-chip v-if="recipe.favorite" color="warning" variant="tonal" prepend-icon="mdi-star">Favorit</v-chip>
              <v-chip v-if="recipe.category" variant="tonal" prepend-icon="mdi-tag-outline">{{ recipe.category }}</v-chip>
              <v-chip v-for="tag in recipe.tags" :key="tag" size="small" variant="outlined">{{ tag }}</v-chip>
            </div>

            <h1>{{ recipe.title }}</h1>
            <div class="recipe-meta-grid">
              <div><v-icon>mdi-clock-start</v-icon><span><small>Vorbereitung</small><strong>{{ recipe.preparation_minutes ?? 0 }} Min.</strong></span></div>
              <div><v-icon>mdi-stove</v-icon><span><small>Zubereitung</small><strong>{{ recipe.cooking_minutes ?? 0 }} Min.</strong></span></div>
              <div><v-icon>mdi-clock-outline</v-icon><span><small>Gesamt</small><strong>{{ totalMinutes }} Min.</strong></span></div>
            </div>
          </div>
          <v-img v-if="recipe.image_url" class="recipe-hero-image" :src="recipe.image_url" cover />
          <div v-else class="recipe-hero-placeholder"><v-icon size="72">mdi-food</v-icon></div>
        </div>

        <div class="recipe-detail-content">
          <section class="ingredients-column">
            <div class="section-heading ingredients-heading">
              <div><h2>Zutaten</h2><span>Für {{ portions }} Portionen</span></div>
              <div class="detail-portion-stepper">
                <v-btn icon="mdi-minus" size="small" variant="text" aria-label="Eine Portion weniger" @click="adjustPortions(-1)" />
                <strong>{{ portions }}</strong>
                <v-btn icon="mdi-plus" size="small" variant="text" aria-label="Eine Portion mehr" @click="adjustPortions(1)" />
              </div>
            </div>

            <v-list class="ingredient-detail-list" bg-color="transparent" lines="two">
              <v-list-item v-for="(ingredient, index) in scaledIngredients" :key="`${ingredient.name}-${index}`" class="px-0">
                <template #prepend><v-icon size="18" color="primary">mdi-circle-small</v-icon></template>
                <v-list-item-title>
                  <strong v-if="ingredient.amount !== null || ingredient.unit" class="ingredient-quantity">{{ formatAmount(ingredient.amount) }}{{ ingredient.amount !== null && ingredient.unit ? ' ' : '' }}{{ ingredient.unit }}</strong>{{ ingredient.name }}
                </v-list-item-title>
                <v-list-item-subtitle v-if="ingredient.note">{{ ingredient.note }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </section>

          <section class="steps-column">
            <div class="section-heading"><div><h2>Zubereitung</h2><span>{{ recipe.steps.length }} Schritte</span></div></div>
            <div class="detail-steps">
              <v-card v-for="(step, index) in recipe.steps" :key="`${index}-${step}`" class="detail-step" variant="outlined">
                <v-card-text>
                  <div class="detail-step-number">{{ index + 1 }}</div>
                  <div><strong>Schritt {{ index + 1 }}</strong><p>{{ step }}</p></div>
                </v-card-text>
              </v-card>
            </div>

            <v-card v-if="recipe.notes" class="mt-4" variant="tonal">
              <v-card-title class="text-subtitle-1"><v-icon class="mr-2">mdi-note-text-outline</v-icon>Notizen</v-card-title>
              <v-card-text class="recipe-notes-text">{{ recipe.notes }}</v-card-text>
            </v-card>
          </section>
        </div>
      </v-card-text>

      <v-divider />
      <v-card-actions class="recipe-detail-actions pa-3">
        <v-btn v-if="recipe.source_url" :href="recipe.source_url" target="_blank" rel="noopener" prepend-icon="mdi-open-in-new" variant="text">Quelle</v-btn>
        <v-spacer />
        <v-btn prepend-icon="mdi-printer" variant="text" @click="emit('print')">Drucken</v-btn>
        <v-btn prepend-icon="mdi-pencil" variant="tonal" @click="emit('edit')">Bearbeiten</v-btn>
        <v-btn color="primary" prepend-icon="mdi-chef-hat" @click="emit('cook')">Kochmodus</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.recipe-detail-card { max-height: calc(100dvh - 24px); }
.recipe-detail-body { overflow-y: auto; -webkit-overflow-scrolling: touch; }
.recipe-hero { display: grid; grid-template-columns: minmax(0, 1.05fr) minmax(320px, .95fr); min-height: 280px; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.recipe-hero-copy { display: flex; flex-direction: column; justify-content: center; padding: 32px; }
.recipe-hero-copy h1 { margin: 0 0 24px; font-size: clamp(1.75rem, 3vw, 2.5rem); line-height: 1.08; }
.recipe-hero-image { min-height: 280px; }
.recipe-hero-placeholder { display: grid; place-items: center; min-height: 280px; color: rgba(var(--v-theme-on-surface), .2); background: rgba(var(--v-theme-primary), .04); }
.recipe-meta-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.recipe-meta-grid > div { display: flex; align-items: center; gap: 10px; min-width: 0; padding: 12px; border-radius: 12px; background: rgba(var(--v-theme-primary), .06); }
.recipe-meta-grid .v-icon { color: rgb(var(--v-theme-primary)); }
.recipe-meta-grid span { display: grid; min-width: 0; }
.recipe-meta-grid small { color: rgba(var(--v-theme-on-surface), .6); }
.recipe-meta-grid strong { font-size: .92rem; white-space: nowrap; }
.recipe-detail-content { display: grid; grid-template-columns: minmax(270px, .8fr) minmax(0, 1.55fr); }
.ingredients-column, .steps-column { padding: 28px; }
.ingredients-column { border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.section-heading { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.section-heading h2 { margin: 0; font-size: 1.3rem; }
.section-heading span { color: rgba(var(--v-theme-on-surface), .6); font-size: .82rem; }
.ingredients-heading > div:first-child { display: grid; }
.detail-portion-stepper { display: flex; align-items: center; gap: 3px; min-height: 42px; padding: 2px 4px; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 12px; }
.detail-portion-stepper strong { min-width: 32px; text-align: center; }
.ingredient-detail-list { padding: 0; }
.ingredient-quantity { margin-right: .35em; }
.detail-steps { display: grid; gap: 10px; }
.detail-step { border-radius: 14px; }
.detail-step .v-card-text { display: grid; grid-template-columns: 38px minmax(0, 1fr); gap: 12px; align-items: start; padding: 16px; }
.detail-step-number { display: grid; place-items: center; width: 34px; height: 34px; border-radius: 10px; background: rgba(var(--v-theme-primary), .13); color: rgb(var(--v-theme-primary)); font-weight: 800; }
.detail-step p { margin: 5px 0 0; line-height: 1.5; white-space: pre-wrap; }
.recipe-notes-text { white-space: pre-wrap; }
.recipe-detail-actions { flex-wrap: wrap; }

@media (max-width: 900px) {
  .recipe-hero { grid-template-columns: 1fr; }
  .recipe-hero-copy { padding: 24px; }
  .recipe-hero-image, .recipe-hero-placeholder { min-height: 230px; order: -1; }
  .recipe-detail-content { grid-template-columns: 1fr; }
  .ingredients-column { border-right: 0; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
}

@media (max-width: 600px) {
  .recipe-hero-copy, .ingredients-column, .steps-column { padding: 18px; }
  .recipe-meta-grid { grid-template-columns: 1fr; }
  .recipe-detail-actions .v-btn { flex: 1 1 auto; }
}
</style>
