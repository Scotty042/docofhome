import vm from 'node:vm'
import ts from 'typescript'
import { computed, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import source from './TimeExportCard.vue?raw'
const config = {enabled:false,upload_to_nextcloud:false,nextcloud_folder:'DocOfHome/Zeiterfassung',last_exported_month:null,last_success_at:null,last_error:null}
const response = (body:unknown,ok=true)=>({ok,json:async()=>body})
function card() {
  let script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)![1]
  const ast = ts.createSourceFile('Card.ts',script,ts.ScriptTarget.Latest,true)
  for (const statement of [...ast.statements].reverse()) if (ts.isImportDeclaration(statement)) script=script.slice(0,statement.pos)+script.slice(statement.end)
  const fetch=vi.fn(),sandbox={ref,computed,fetch,onMounted(){}}
  vm.createContext(sandbox)
  const compiled=ts.transpileModule(script,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}}).outputText
  const state=vm.runInContext(compiled+'\n({form,configuration,files,busy,error,notice,dirty,act})',sandbox)
  return {state,fetch}
}
describe('monthly time export settings',()=>{
  it('starts disabled, saves explicit options and uses a separate run request',async()=>{
    const {state,fetch}=card()
    fetch.mockResolvedValueOnce(response({configuration:config,files:[]}))
    await state.act('load')
    expect(state.form.value.enabled).toBe(false)
    state.form.value.enabled=true
    expect(state.dirty.value).toBe(true)
    const enabled={...config,enabled:true}
    fetch.mockResolvedValueOnce(response(enabled)).mockResolvedValueOnce(response({configuration:enabled,files:[]}))
    await state.act('save')
    expect(fetch.mock.calls[1]![0]).toBe('/api/v1/time-exports/configuration')
    expect(JSON.parse(fetch.mock.calls[1]![1].body).enabled).toBe(true)
    expect(state.dirty.value).toBe(false)
    fetch.mockResolvedValueOnce(response(enabled)).mockResolvedValueOnce(response({configuration:enabled,files:[{filename:'docofhome-zeiten-2026-10.csv',month:'2026-10',size_bytes:100}]}))
    await state.act('run')
    expect(fetch.mock.calls[3]![1].method).toBe('POST')
    expect(state.files.value).toHaveLength(1)
  })
  it('shows failed upload status while retaining the local download',async()=>{
    const {state,fetch}=card(),failed={...config,last_error:'Nextcloud upload failed (403)'}
    fetch.mockResolvedValueOnce(response(failed)).mockResolvedValueOnce(response({configuration:failed,files:[{filename:'docofhome-zeiten-2026-10.csv',month:'2026-10',size_bytes:100}]}))
    await state.act('run')
    expect(state.configuration.value.last_error).toContain('403')
    expect(state.files.value).toHaveLength(1)
    expect(state.notice.value).toBe('')
  })
})
