import vm from 'node:vm'
import ts from 'typescript'
import { computed, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import source from './NotificationSettingsPage.vue?raw'
import { defaultPushConfig, editablePushConfig } from '../types/notifications'
import type { PushRead } from '../types/notifications'

function page() {
  let script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)![1]
  const ast = ts.createSourceFile('Push.ts', script, ts.ScriptTarget.Latest, true)
  for (const statement of [...ast.statements].reverse()) {
    if (ts.isImportDeclaration(statement)) script = script.slice(0, statement.pos) + script.slice(statement.end)
  }
  const saved = { ...defaultPushConfig(), pushover_app_token_configured: true, pushover_user_key_configured: true, ntfy_access_token_configured: false } as PushRead
  const save = vi.fn(async () => saved)
  const test = vi.fn(async () => ({ success: true, message: 'Accepted' }))
  let leave = () => true
  const sandbox = { ref, computed, onMounted() {}, onBeforeUnmount() {}, onBeforeRouteLeave(fn: () => boolean) { leave = fn },
    window: { confirm: vi.fn(() => true), addEventListener() {}, removeEventListener() {} },
    useSettingsStore: () => ({ configuration: { timezone: 'Europe/Berlin' } }),
    defaultPushConfig, editablePushConfig, notificationApi: { save, test, history: async () => [] } }
  vm.createContext(sandbox)
  const compiled = ts.transpileModule(script, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None } }).outputText
  const state = vm.runInContext(compiled + '\n({ form, loading, stored, dirty, accept, save, test, discard, payload, beforeUnload, sendTime })', sandbox)
  state.accept(saved); state.loading.value = false
  return { state, save, test, leave: () => leave() }
}

describe('push settings', () => {
  it('defaults to disabled and omits read-only credential flags from the draft', () => {
    const { state } = page()
    expect(state.form.value.enabled).toBe(false)
    expect(state.form.value).not.toHaveProperty('pushover_app_token_configured')
    expect(state.form.value).not.toHaveProperty('pushover_app_token')
  })
  it('tests the unsaved draft without saving or clearing dirty changes', async () => {
    const { state, save, test } = page()
    state.form.value.ntfy_topic = 'private-topic'
    await state.test('ntfy')
    expect(test).toHaveBeenCalledWith('ntfy', expect.objectContaining({ ntfy_topic: 'private-topic' }))
    expect(save).not.toHaveBeenCalled(); expect(state.dirty.value).toBe(true)
  })
  it('clears entered secrets on save and removes a token marked for deletion', async () => {
    const { state, save } = page()
    state.form.value.pushover_app_token = 'temporary-secret'
    state.form.value.clear_pushover_app_token = true
    expect(state.payload()).not.toHaveProperty('pushover_app_token')
    await state.save()
    expect(save).toHaveBeenCalledOnce()
    expect(state.form.value).not.toHaveProperty('pushover_app_token')
    expect(state.dirty.value).toBe(false)
  })
  it('keeps the draft when saving fails and allows discarding it', async () => {
    const { state, save } = page()
    save.mockRejectedValueOnce(new Error('Failed'))
    state.form.value.ntfy_topic = 'unsaved'
    await state.save(); expect(state.dirty.value).toBe(true)
    state.discard(); expect(state.form.value.ntfy_topic).toBe('')
  })
  it('warns on browser unload and offers navigation confirmation only for changes', () => {
    const { state, leave } = page()
    const event = { preventDefault: vi.fn(), returnValue: undefined }
    state.beforeUnload(event); expect(event.preventDefault).not.toHaveBeenCalled()
    state.form.value.send_hour = 10
    state.beforeUnload(event); expect(event.preventDefault).toHaveBeenCalled()
    expect(leave()).toBe(true)
    state.sendTime.value = '06:45'
    expect(state.form.value.send_hour).toBe(6)
    expect(state.form.value.send_minute).toBe(45)
  })
})
