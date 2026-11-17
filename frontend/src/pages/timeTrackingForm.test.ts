import vm from 'node:vm'
import ts from 'typescript'
import { computed, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import source from './TimeTrackingPage.vue?raw'
import * as presentation from '../services/timeTracking'

function page() {
  let script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)![1]
  const ast = ts.createSourceFile('TimeTracking.ts', script, ts.ScriptTarget.Latest, true)
  for (const statement of [...ast.statements].reverse()) {
    if (ts.isImportDeclaration(statement)) script = script.slice(0, statement.pos) + script.slice(statement.end)
  }
  const fetch = vi.fn()
  const sandbox = { ...presentation, duration: presentation.formatDuration, ref, computed, fetch,
    onMounted() {}, onUnmounted() {} }
  vm.createContext(sandbox)
  const compiled = ts.transpileModule(script, {
    compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None }
  }).outputText
  const state = vm.runInContext(compiled + '\n({ticket, customer, info, items, active, busy, error, finish, act, updateBcs})', sandbox)
  state.ticket.value = 'T-123'; state.customer.value = 'Kunde'; state.info.value = 'Analyse'
  const running = { id: 'run-1', ticket: 'T-123', customer: 'Kunde', info: 'Analyse',
    started_at: 1000, ended_at: null, running: true, completed: false, bcs: false }
  state.items.value = [running]
  return { state, fetch, running }
}
const response = (body: unknown, ok = true) => ({ ok, status: ok ? 200 : 409, json: async () => body })

describe('time tracking form after ending a task', () => {
  it('clears all three fields only after the server confirms end and keeps the saved entry', async () => {
    const { state, fetch, running } = page()
    const ended = { ...running, running: false, completed: true, ended_at: 2000 }
    fetch.mockResolvedValueOnce(response(ended)).mockResolvedValueOnce(response([ended]))
    state.finish()
    await vi.waitFor(() => expect(state.busy.value).toBe(false))
    expect(fetch.mock.calls[0]![0]).toBe('/api/v1/time-tracking/run-1/end')
    expect([state.ticket.value, state.customer.value, state.info.value]).toEqual(['', '', ''])
    expect(state.active.value).toBeUndefined()
    expect(state.items.value[0]).toMatchObject({ ticket: 'T-123', customer: 'Kunde', completed: true })
  })
  it('preserves the fields on an unsuccessful end', async () => {
    const { state, fetch, running } = page()
    fetch.mockResolvedValueOnce(response({ detail: 'Speichern fehlgeschlagen' }, false))
      .mockResolvedValueOnce(response([running]))
    state.finish()
    await vi.waitFor(() => expect(state.busy.value).toBe(false))
    expect([state.ticket.value, state.customer.value, state.info.value]).toEqual(['T-123', 'Kunde', 'Analyse'])
    expect(state.error.value).toBe('Speichern fehlgeschlagen')
  })
  it('keeps the fields after pause', async () => {
    const { state, fetch, running } = page()
    const paused = { ...running, running: false, ended_at: 2000 }
    fetch.mockResolvedValueOnce(response(paused)).mockResolvedValueOnce(response([paused]))
    await state.act('/run-1/pause')
    expect([state.ticket.value, state.customer.value, state.info.value]).toEqual(['T-123', 'Kunde', 'Analyse'])
  })
  it('clears and unlocks the form after a confirmed end even if refreshing fails', async () => {
    const { state, fetch, running } = page()
    const ended = { ...running, running: false, completed: true, ended_at: 2000 }
    fetch.mockResolvedValueOnce(response(ended)).mockRejectedValue(new Error('Verbindung unterbrochen'))
    state.finish()
    await vi.waitFor(() => expect(state.busy.value).toBe(false))
    expect([state.ticket.value, state.customer.value, state.info.value]).toEqual(['', '', ''])
    expect(state.active.value).toBeUndefined()
    expect(state.items.value[0]).toMatchObject({ id: 'run-1', completed: true })
  })
})


describe('BCS checkbox saving', () => {
  it('saves just BCS and preserves the active timer', async () => {
    const {state,fetch,running}=page()
    fetch.mockResolvedValueOnce(response({...running,bcs:true}))
    await state.updateBcs(running,true)
    expect(fetch.mock.calls[0]![0]).toBe('/api/v1/time-tracking/run-1/bcs')
    expect(fetch.mock.calls[0]![1]).toMatchObject({method:'PATCH',body:'{"bcs":true}'})
    expect(state.items.value[0].bcs).toBe(true)
    expect(state.active.value.id).toBe('run-1')
  })
  it('does not retain a checkmark when saving fails', async () => {
    const {state,fetch,running}=page()
    fetch.mockResolvedValueOnce(response({detail:'Speichern fehlgeschlagen'},false))
    await state.updateBcs(running,true)
    expect(state.items.value[0].bcs).toBe(false)
    expect(state.error.value).toBe('Speichern fehlgeschlagen')
    expect(state.busy.value).toBe(false)
  })
})
