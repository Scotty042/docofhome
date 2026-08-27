import { describe, expect, it } from 'vitest'

import cookbook from './CookbookPage.vue?raw'
import cookMode from '../components/RecipeCookMode.vue?raw'
import detailDialog from '../components/RecipeDetailDialog.vue?raw'
import editorDialog from '../components/RecipeEditorDialog.vue?raw'
import imageField from '../components/RecipeImageField.vue?raw'

describe('release 1.7.13.3 cookbook tablet experience', () => {
  it('keeps the normal recipe view inside DocOfHome and makes only cooking immersive', () => {
    expect(cookbook).toContain('RecipeDetailDialog')
    expect(cookbook).toContain('RecipeCookMode')
    expect(cookMode).toContain('position: fixed')
    expect(cookMode).toContain('100dvh')
    expect(cookMode).toContain('grid-template-columns: minmax(290px, .72fr) minmax(0, 1.65fr)')
    expect(detailDialog).toContain('max-width="1220"')
  })

  it('provides cooking touch controls, wake lock and portion scaling', () => {
    expect(cookMode).toContain('Bildschirm nicht abschalten')
    expect(cookMode).toContain("wakeLock.request('screen')")
    expect(cookMode).toContain('checkedIngredients')
    expect(cookMode).toContain('checkedSteps')
    expect(cookMode).toContain("emit('update:portions'")
  })

  it('uses autocomplete and touch-accessible ordering in the ingredient editor', () => {
    expect(editorDialog).toContain(':items="unitSuggestions"')
    expect(editorDialog).toContain(':items="ingredientSuggestions"')
    expect(editorDialog).toContain('mdi-drag-vertical')
    expect(editorDialog).toContain('Nach oben')
    expect(editorDialog).toContain('Nach unten')
    expect(editorDialog).toContain('Löschen')
  })

  it('uses local camera/file uploads and Immich instead of a normal image URL field', () => {
    expect(editorDialog).toContain('RecipeImageField')
    expect(editorDialog).not.toContain('label="Bild-URL (optional)"')
    expect(imageField).toContain('Foto aufnehmen')
    expect(imageField).toContain('Bild auswählen')
    expect(imageField).toContain('Aus Immich auswählen')
    expect(imageField).toContain('capture="environment"')
    expect(imageField).toContain('Erweitert')
  })

  it('keeps a visible gap between quantity/unit and ingredient name', () => {
    expect(detailDialog).toContain('class="ingredient-quantity"')
    expect(detailDialog).toContain('margin-right: .35em')
  })
})
