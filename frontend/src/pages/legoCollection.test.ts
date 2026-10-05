import vm from 'node:vm'
import ts from 'typescript'
import { computed, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import source from './LegoPage.vue?raw'
import { emptyLegoSet, editableLegoSet, legoDimensions, buildStatuses } from '../types/lego'
import type { LegoSet } from '../types/lego'
import { legoApi } from '../services/legoApi'

function page() {
  let script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)![1]
  const ast = ts.createSourceFile('LegoPage.ts', script, ts.ScriptTarget.Latest, true)
  for (const statement of [...ast.statements].reverse()) {
    if (ts.isImportDeclaration(statement)) script = script.slice(0, statement.pos) + script.slice(statement.end)
  }
  let guard: () => boolean = () => true
  const confirm = vi.fn(() => false)
  const create = vi.fn(async () => ({}))
  const update = vi.fn(async () => ({}))
  const sandbox = { computed, ref, onMounted() {}, onBeforeUnmount() {}, onBeforeRouteLeave(fn: () => boolean) { guard = fn },
    window: { addEventListener() {}, removeEventListener() {}, confirm },
    useNotificationStore: () => ({ success() {}, warning() {} }), emptyLegoSet, editableLegoSet, legoDimensions, buildStatuses,
    legoApi: { create, update, list: async () => [], dashboard: async () => ({ sets_count: 0 }) }, locationApi: {} }
  vm.createContext(sandbox)
  const compiled = ts.transpileModule(script, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText
  const state = vm.runInContext(compiled + '\n({ items, visible, query, status, form, editor, dirty, open, close, save, leave })', sandbox)
  return { state, confirm, create, update, guard: () => guard() }
}

describe('LEGO collection', () => {
  it('keeps nullable dimensions unknown and strips read-only fields for editing', () => {
    expect(legoDimensions(emptyLegoSet())).toBe('Maße nicht erfasst')
    expect(legoDimensions({ ...emptyLegoSet(), width_cm: 44 })).toContain('44 × – × –')
    expect(editableLegoSet({ ...emptyLegoSet(), id: 'test' } as LegoSet)).not.toHaveProperty('id')
  })
  it('filters real page state by query and build status', () => {
    const { state } = page()
    state.items.value = [{ ...emptyLegoSet(), set_number: '10305', name: 'Castle', build_status: 'built' }, { ...emptyLegoSet(), set_number: '21338', name: 'Cabin' }]
    state.query.value = '10305'; expect(state.visible.value).toHaveLength(1)
    state.status.value = 'sealed'; expect(state.visible.value).toHaveLength(0)
  })
  it('protects unsaved changes on close, navigation and reload', () => {
    const { state, guard } = page()
    state.open(); state.form.value.name = 'Unsaved'
    expect(state.dirty.value).toBe(true)
    state.close(); expect(state.editor.value).toBe(true)
    expect(guard()).toBe(false)
    const event = { preventDefault: vi.fn(), returnValue: undefined }
    state.leave(event); expect(event.preventDefault).toHaveBeenCalled()
  })
  it('saves without turning unknown numeric fields into zero', async () => {
    const { state, create } = page()
    state.open(); state.form.value.set_number = '10305'; state.form.value.name = 'Castle'
    await state.save()
    expect(create).toHaveBeenCalledWith(expect.objectContaining({ purchase_price: null, parts_count: null, width_cm: null }))
    expect(state.editor.value).toBe(false)
  })
  it('loads all pages instead of silently stopping at 100 sets', async () => {
    const spy = vi.spyOn(legoApi, 'page').mockResolvedValueOnce({ items: [{ id: 'a' } as LegoSet], total: 2, count: 1, has_more: true, next_offset: 1 }).mockResolvedValueOnce({ items: [{ id: 'b' } as LegoSet], total: 2, count: 1, has_more: false, next_offset: null })
    expect((await legoApi.list()).map(s => s.id)).toEqual(['a', 'b'])
    expect(spy).toHaveBeenLastCalledWith(1); spy.mockRestore()
  })
})
