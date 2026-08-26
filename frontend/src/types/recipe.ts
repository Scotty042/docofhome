export interface Ingredient { amount: number | null; unit: string; name: string; note: string }
export interface Recipe {
  id: string; title: string; category: string; tags: string[]
  preparation_minutes: number | null; cooking_minutes: number | null; servings: number
  favorite: boolean; image_url: string | null; ingredients: Ingredient[]; steps: string[]
  notes: string; source_url: string | null; attachments: string[]; created_at: string; updated_at: string
}
export type RecipeWrite = Omit<Recipe, 'id' | 'created_at' | 'updated_at'>
