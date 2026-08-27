<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Recipe } from '../types/recipe'

interface WakeLockSentinelLike extends EventTarget {
  release: () => Promise<void>
  released?: boolean
}

interface WakeLockNavigator extends Navigator {
  wakeLock?: {
    request: (type: 'screen') => Promise<WakeLockSentinelLike>
  }
}

const props = defineProps<{
  recipe: Recipe
  portions: number
}>()

const emit = defineEmits<{
  (event: 'update:portions', value: number): void
  (event: 'close'): void
}>()

const checkedIngredients = ref<Set<number>>(new Set())
const checkedSteps = ref<Set<number>>(new Set())
const keepScreenAwake = ref(true)
const wakeLockSupported = ref(false)
const wakeLockActive = ref(false)
let wakeLockSentinel: WakeLockSentinelLike | null = null

const totalMinutes = computed(() => (props.recipe.preparation_minutes ?? 0) + (props.recipe.cooking_minutes ?? 0))
const scaledIngredients = computed(() => {
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

function toggleIngredient(index: number) {
  const next = new Set(checkedIngredients.value)
  if (next.has(index)) next.delete(index)
  else next.add(index)
  checkedIngredients.value = next
}

function toggleStep(index: number) {
  const next = new Set(checkedSteps.value)
  if (next.has(index)) next.delete(index)
  else next.add(index)
  checkedSteps.value = next
}

async function acquireWakeLock() {
  if (!keepScreenAwake.value || document.visibilityState !== 'visible') return
  const wakeLock = (navigator as WakeLockNavigator).wakeLock
  if (!wakeLock || wakeLockSentinel) return
  try {
    wakeLockSentinel = await wakeLock.request('screen')
    wakeLockActive.value = true
    wakeLockSentinel.addEventListener('release', () => {
      wakeLockSentinel = null
      wakeLockActive.value = false
    }, { once: true })
  } catch {
    wakeLockActive.value = false
  }
}

async function releaseWakeLock() {
  const sentinel = wakeLockSentinel
  wakeLockSentinel = null
  wakeLockActive.value = false
  if (sentinel && !sentinel.released) {
    try { await sentinel.release() } catch { /* Browser beendet Wake Lock gegebenenfalls selbst. */ }
  }
}

async function handleVisibilityChange() {
  if (document.visibilityState === 'visible' && keepScreenAwake.value) await acquireWakeLock()
}

watch(keepScreenAwake, async (enabled) => {
  if (enabled) await acquireWakeLock()
  else await releaseWakeLock()
})

onMounted(async () => {
  wakeLockSupported.value = 'wakeLock' in navigator
  document.addEventListener('visibilitychange', handleVisibilityChange)
  if (keepScreenAwake.value) await acquireWakeLock()
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  void releaseWakeLock()
})
</script>

<template>
  <Teleport to="body">
    <div class="recipe-cook-mode" role="dialog" aria-modal="true" :aria-label="`Kochmodus: ${recipe.title}`">
      <header class="cook-header">
        <div class="cook-title-wrap">
          <v-icon size="28" color="primary">mdi-chef-hat</v-icon>
          <div>
            <div class="cook-eyebrow">Kochmodus</div>
            <h1>{{ recipe.title }}</h1>
          </div>
        </div>

        <div class="cook-header-actions">
          <div class="portion-stepper" aria-label="Portionen einstellen">
            <v-btn icon="mdi-minus" variant="text" size="large" aria-label="Eine Portion weniger" @click="adjustPortions(-1)" />
            <div class="portion-value"><strong>{{ portions }}</strong><span>Portionen</span></div>
            <v-btn icon="mdi-plus" variant="text" size="large" aria-label="Eine Portion mehr" @click="adjustPortions(1)" />
          </div>
          <v-btn
            class="cook-close"
            icon="mdi-close"
            color="primary"
            size="large"
            aria-label="Kochmodus beenden"
            title="Kochmodus beenden"
            @click="emit('close')"
          />
        </div>
      </header>

      <main class="cook-content">
        <aside class="ingredients-panel">
          <div class="panel-heading">
            <div>
              <h2>Zutaten</h2>
              <p>Antippen, sobald eine Zutat erledigt ist.</p>
            </div>
          </div>

          <div class="ingredient-list">
            <button
              v-for="(ingredient, index) in scaledIngredients"
              :key="`${ingredient.name}-${index}`"
              type="button"
              class="cook-ingredient"
              :class="{ done: checkedIngredients.has(index) }"
              @click="toggleIngredient(index)"
            >
              <v-icon class="ingredient-check" size="28">
                {{ checkedIngredients.has(index) ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline' }}
              </v-icon>
              <span class="ingredient-text">
                <strong v-if="ingredient.amount !== null || ingredient.unit">
                  {{ formatAmount(ingredient.amount) }}{{ ingredient.amount !== null && ingredient.unit ? ' ' : '' }}{{ ingredient.unit }}
                </strong>
                <span class="ingredient-name">{{ ingredient.name }}</span>
                <small v-if="ingredient.note">{{ ingredient.note }}</small>
              </span>
            </button>
          </div>

          <div class="cook-controls">
            <v-switch
              v-model="keepScreenAwake"
              color="primary"
              hide-details
              :disabled="!wakeLockSupported"
              :label="wakeLockSupported ? 'Bildschirm nicht abschalten' : 'Bildschirm-Wachhalten nicht verfügbar'"
            />
            <div v-if="wakeLockSupported && keepScreenAwake" class="wake-state text-medium-emphasis">
              <v-icon size="18">{{ wakeLockActive ? 'mdi-lightbulb-on-outline' : 'mdi-lightbulb-outline' }}</v-icon>
              {{ wakeLockActive ? 'Bildschirm bleibt aktiv' : 'Wake Lock wird angefordert' }}
            </div>
            <div v-if="totalMinutes" class="cook-time text-medium-emphasis">
              <v-icon size="18">mdi-clock-outline</v-icon>
              Gesamtzeit {{ totalMinutes }} Min.
            </div>
          </div>
        </aside>

        <section class="steps-panel">
          <div class="panel-heading">
            <div>
              <h2>Zubereitung</h2>
              <p>Schritte können beim Kochen als erledigt markiert werden.</p>
            </div>
          </div>

          <div class="cook-steps">
            <button
              v-for="(step, index) in recipe.steps"
              :key="`${index}-${step}`"
              type="button"
              class="cook-step"
              :class="{ done: checkedSteps.has(index) }"
              @click="toggleStep(index)"
            >
              <span class="step-number">{{ index + 1 }}</span>
              <span class="step-copy">
                <strong>Schritt {{ index + 1 }}</strong>
                <span>{{ step }}</span>
              </span>
              <v-icon class="step-check" size="24">
                {{ checkedSteps.has(index) ? 'mdi-check-circle' : 'mdi-circle-outline' }}
              </v-icon>
            </button>
          </div>

          <v-card v-if="recipe.notes" class="cook-notes" variant="tonal">
            <v-card-title class="text-subtitle-1"><v-icon class="mr-2">mdi-note-text-outline</v-icon>Notizen</v-card-title>
            <v-card-text class="recipe-notes-text">{{ recipe.notes }}</v-card-text>
          </v-card>
        </section>
      </main>
    </div>
  </Teleport>
</template>

<style scoped>
.recipe-cook-mode {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: rgb(var(--v-theme-background));
  color: rgb(var(--v-theme-on-background));
}

.cook-header {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  min-height: 86px;
  padding: max(12px, env(safe-area-inset-top)) max(18px, env(safe-area-inset-right)) 12px max(18px, env(safe-area-inset-left));
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgb(var(--v-theme-surface));
}

.cook-title-wrap,
.cook-header-actions,
.portion-stepper,
.panel-heading,
.wake-state,
.cook-time {
  display: flex;
  align-items: center;
}

.cook-title-wrap { gap: 12px; min-width: 0; }
.cook-title-wrap h1 { margin: 0; font-size: clamp(1.2rem, 2vw, 1.8rem); line-height: 1.15; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.cook-eyebrow { color: rgb(var(--v-theme-primary)); font-size: .75rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
.cook-header-actions { gap: 12px; flex: 0 0 auto; }
.portion-stepper { min-height: 54px; border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); border-radius: 16px; background: rgb(var(--v-theme-background)); }
.portion-value { min-width: 86px; text-align: center; line-height: 1.05; }
.portion-value strong { display: block; font-size: 1.12rem; }
.portion-value span { display: block; margin-top: 4px; color: rgba(var(--v-theme-on-background), .65); font-size: .72rem; }

.cook-content {
  display: grid;
  grid-template-columns: minmax(290px, .72fr) minmax(0, 1.65fr);
  flex: 1 1 auto;
  min-height: 0;
  overflow: hidden;
}

.ingredients-panel,
.steps-panel {
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  padding: 24px;
}

.ingredients-panel {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  background: rgba(var(--v-theme-surface), .38);
}

.panel-heading { justify-content: space-between; margin-bottom: 16px; }
.panel-heading h2 { margin: 0; font-size: 1.35rem; }
.panel-heading p { margin: 4px 0 0; color: rgba(var(--v-theme-on-background), .62); font-size: .86rem; }
.ingredient-list,
.cook-steps { display: grid; gap: 10px; }

.cook-ingredient,
.cook-step {
  width: 100%;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 14px;
  background: rgb(var(--v-theme-surface));
  color: inherit;
  text-align: left;
  touch-action: manipulation;
}

.cook-ingredient {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-height: 58px;
  padding: 14px;
}

.ingredient-check { flex: 0 0 auto; margin-top: 1px; color: rgb(var(--v-theme-primary)); }
.ingredient-text { display: block; min-width: 0; font-size: 1rem; line-height: 1.3; }
.ingredient-text strong { margin-right: .45em; }
.ingredient-name { font-weight: 600; }
.ingredient-text small { display: block; margin-top: 4px; color: rgba(var(--v-theme-on-background), .62); font-size: .82rem; }
.cook-ingredient.done .ingredient-text { opacity: .48; text-decoration: line-through; }

.cook-controls { display: grid; gap: 8px; margin-top: 22px; padding-top: 16px; border-top: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
.wake-state,
.cook-time { gap: 7px; font-size: .8rem; }

.steps-panel { padding-bottom: max(24px, env(safe-area-inset-bottom)); }
.cook-step {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) 30px;
  gap: 14px;
  align-items: start;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, .08);
}
.step-number { display: grid; place-items: center; width: 42px; height: 42px; border-radius: 12px; background: rgba(var(--v-theme-primary), .13); color: rgb(var(--v-theme-primary)); font-size: 1.05rem; font-weight: 800; }
.step-copy { display: grid; gap: 7px; min-width: 0; font-size: 1rem; line-height: 1.55; }
.step-copy strong { font-size: 1.05rem; }
.step-check { margin-top: 8px; color: rgb(var(--v-theme-primary)); }
.cook-step.done { opacity: .56; }
.cook-step.done .step-copy span { text-decoration: line-through; }
.cook-notes { margin-top: 18px; }
.recipe-notes-text { white-space: pre-wrap; }

@media (max-width: 900px), (orientation: portrait) and (max-width: 1100px) {
  .recipe-cook-mode { overflow-y: auto; }
  .cook-header { position: sticky; top: 0; flex-wrap: wrap; }
  .cook-content { display: block; overflow: visible; }
  .ingredients-panel,
  .steps-panel { overflow: visible; padding: 20px; }
  .ingredients-panel { border-right: 0; border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity)); }
}

@media (max-width: 620px) {
  .cook-header { gap: 10px; min-height: 72px; padding-left: 12px; padding-right: 12px; }
  .cook-title-wrap { width: calc(100% - 58px); }
  .cook-title-wrap > .v-icon { display: none; }
  .cook-header-actions { width: 100%; justify-content: space-between; }
  .portion-stepper { flex: 1 1 auto; justify-content: center; }
  .cook-close { position: absolute; top: max(10px, env(safe-area-inset-top)); right: 10px; }
  .ingredients-panel,
  .steps-panel { padding: 14px; }
  .panel-heading p { display: none; }
  .cook-step { grid-template-columns: 38px minmax(0, 1fr) 26px; gap: 10px; padding: 14px; }
  .step-number { width: 36px; height: 36px; }
}
</style>
