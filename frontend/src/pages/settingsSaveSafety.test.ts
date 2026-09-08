import vm from 'node:vm'
import ts from 'typescript'
import { ref, computed } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import source from './SettingsPage.vue?raw'

// Execute the page's actual script with Vue reactivity and isolated I/O.
function page() {
  const script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)![1]
  const ast = ts.createSourceFile('SettingsPage.ts', script, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
  let stripped = script
  for (const statement of [...ast.statements].reverse()) {
    if (ts.isImportDeclaration(statement)) stripped = stripped.slice(0, statement.pos) + stripped.slice(statement.end)
  }
  const defaults = () => ({ application: { installation_name: 'Original' }, integrations: [{ kind: 'paperless', enabled: true, base_url: 'http://paperless.test' }] })
  const clone = (value: unknown) => JSON.parse(JSON.stringify(value))
  const saveConfiguration = vi.fn(async (value: unknown) => clone(value))
  const testIntegrationDraft = vi.fn(async () => ({ success: true }))
  const updateMcp = vi.fn(async () => { throw new Error('MCP save failed') })
  const sandbox = {
    ref, computed, onMounted() {}, onBeforeUnmount() {}, onBeforeRouteLeave() {},
    window: { location: { origin: 'http://test' }, addEventListener() {} },
    useSettingsStore: () => ({ configuration: defaults(), saveConfiguration }),
    createDefaultConfiguration: defaults, editableConfiguration: clone,
    settingsApi: { testIntegrationDraft, updateMcp }
  }
  vm.createContext(sandbox)
  const compiled = ts.transpileModule(stripped, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText
  const state = vm.runInContext(compiled + '\n({form, mcpForm, loading, dirty, testIntegration, discardChanges, save, warnBeforeUnload})', sandbox)
  state.loading.value = false
  return { state, saveConfiguration, testIntegrationDraft, updateMcp }
}

describe('settings save safety', () => {
  it('tests a draft without saving unrelated changes and can discard it', async () => {
    const { state, saveConfiguration, testIntegrationDraft } = page()
    state.form.value.application.installation_name = 'Unsaved'
    await state.testIntegration('paperless')
    expect(testIntegrationDraft).toHaveBeenCalledOnce()
    expect(saveConfiguration).not.toHaveBeenCalled()
    expect(state.dirty.value).toBe(true)
    state.discardChanges()
    expect(state.form.value.application.installation_name).toBe('Original')
    expect(state.dirty.value).toBe(false)
  })

  it('retains successfully saved general settings after the MCP save fails', async () => {
    const { state, saveConfiguration, updateMcp } = page()
    state.form.value.application.installation_name = 'Saved'
    state.mcpForm.value.permission = 'admin'
    await state.save()
    expect(saveConfiguration).toHaveBeenCalledOnce()
    expect(updateMcp).toHaveBeenCalledOnce()
    expect(state.dirty.value).toBe(true)
    state.discardChanges()
    expect(state.form.value.application.installation_name).toBe('Saved')
    expect(state.mcpForm.value.permission).toBe('read')
    expect(state.dirty.value).toBe(false)
  })

  it('warns on browser unload only while changes remain unsaved', () => {
    const { state } = page()
    const event = { preventDefault: vi.fn(), returnValue: undefined }
    state.warnBeforeUnload(event)
    expect(event.preventDefault).not.toHaveBeenCalled()
    state.form.value.application.installation_name = 'Unsaved'
    state.warnBeforeUnload(event)
    expect(event.preventDefault).toHaveBeenCalledOnce()
    expect(event.returnValue).toBe('')
  })
})
