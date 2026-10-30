import vm from 'node:vm'
import ts from 'typescript'
import { computed, ref } from 'vue'
import { describe, expect, it, vi } from 'vitest'
import source from './FilamentPage.vue?raw'
import { emptySpool, editableSpool, emptyFilamentConfig, editableFilamentConfig } from '../types/filament'
import type { FilamentSpool } from '../types/filament'
import { filamentApi } from '../services/filamentApi'

function page() {
  let script = source.match(/<script setup lang="ts">([\s\S]*?)<\/script>/)![1]
  const ast = ts.createSourceFile('Filament.ts',script,ts.ScriptTarget.Latest,true)
  for (const statement of [...ast.statements].reverse()) if (ts.isImportDeclaration(statement)) script = script.slice(0,statement.pos) + script.slice(statement.end)
  const config = { ...emptyFilamentConfig(), token_configured: false, last_sync: null, last_error: null, last_mqtt: null, mqtt_error: null }
  const storeImage = vi.fn(async (id: string) => ({id, image_url: '/local-image.png'})), create = vi.fn(async () => ({})), loginApi = vi.fn(async () => ({ connected: true, verification_required: false }))
  let leave = () => true
  const sandbox = { ref, computed, watch() {}, onMounted() {}, onBeforeUnmount() {}, onBeforeRouteLeave(fn: () => boolean) { leave = fn }, useRoute: () => ({ params: {} }),
    window: { addEventListener() {},removeEventListener() {},confirm:vi.fn(() => false) },
    emptySpool,editableSpool,emptyFilamentConfig,editableFilamentConfig,
    filamentApi: { create,storeImage,login:loginApi,list:async () => [],slots:async () => [],settings:async () => config }, locationApi: {} }
  vm.createContext(sandbox)
  const compiled=ts.transpileModule(script,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.None}}).outputText
  const state=vm.runInContext(compiled+'\n({ form, items, material, manufacturer, archive, reorder, visible, loading, savedConfig, config, dirty, open, save, login, connect, unload, fillStoreImages, imageIssues })',sandbox)
  state.loading.value=false; state.savedConfig.value=JSON.stringify(state.config.value)
  return {state,create,storeImage,loginApi,leave:() => leave()}
}

describe('filament collection',() => {
  it('keeps technical and archive fields out of manual edit payloads',() => {
    expect(editableSpool({...emptySpool(),id:'x',cloud_id:'42',archived_at:'date'} as FilamentSpool)).not.toHaveProperty('cloud_id')
    expect(emptySpool().remaining_g).toBeNull()
  })
  it('combines material, manufacturer, reorder and archive filters',() => {
    const {state}=page()
    state.items.value=[{...emptySpool(),id:'a',material:'PLA',manufacturer:'SUNLU',reorder:true,archived_at:null},{...emptySpool(),id:'b',material:'ABS',manufacturer:'SUNLU',archived_at:'date'}]
    state.material.value='PLA'; state.manufacturer.value='SUNLU'; state.reorder.value=true
    expect(state.visible.value).toHaveLength(1)
    state.archive.value='archived'; expect(state.visible.value).toHaveLength(0)
  })
  it('saves unknown amounts as null and zero as zero',async () => {
    const {state,create}=page(); state.open(); state.form.value.remaining_g=0
    await state.save()
    expect(create).toHaveBeenCalledWith(expect.objectContaining({remaining_g:0,initial_g:null}))
  })
  it('clears credentials after successful login without retaining a token in settings',async () => {
    const {state,loginApi}=page(); state.login.value={account:'user@example.invalid',password:'secret',code:'',access_token:''}
    await state.connect(); expect(loginApi).toHaveBeenCalledOnce()
    expect(state.login.value.password).toBe(''); expect(state.login.value.access_token).toBe('')
  })
  it('protects unsaved form and connection changes on reload and navigation',() => {
    const {state,leave}=page(); state.open(); state.form.value.material='ASA'
    const event={preventDefault:vi.fn(),returnValue:undefined}; state.unload(event)
    expect(event.preventDefault).toHaveBeenCalled(); expect(leave()).toBe(false)
  })
  it('preserves unsaved URL and printer settings across cloud login',async () => {
    const {state}=page()
    state.config.value.public_url='https://draft.example.test'
    state.config.value.printer_serials=['DRAFT-PRINTER']
    await state.connect()
    expect(state.config.value.public_url).toBe('https://draft.example.test')
    expect(state.config.value.printer_serials).toEqual(['DRAFT-PRINTER'])
    expect(state.dirty.value).toBe(true)
  })
  it('fills missing Bambu pictures without overwriting existing pictures or selecting other brands',async () => {
    const {state,storeImage}=page()
    state.items.value=[{...emptySpool(),id:'a',label_code:'FIL-a',manufacturer:'Bambu Lab',archived_at:null},{...emptySpool(),id:'b',manufacturer:'Bambu Lab',image_url:'/my-photo.png',archived_at:null},{...emptySpool(),id:'c',manufacturer:'SUNLU',archived_at:null},{...emptySpool(),id:'d',manufacturer:'Bambu Lab',archived_at:'old'}]
    await state.fillStoreImages()
    expect(storeImage).toHaveBeenCalledExactlyOnceWith('a')
    expect(state.items.value.find((v: FilamentSpool)=>v.id==='b').image_url).toBe('/my-photo.png')
  })
  it('continues after an unclear image assignment and reports that roll',async () => {
    const {state,storeImage}=page()
    state.items.value=['a','b'].map(id=>({...emptySpool(),id,label_code:'FIL-'+id,manufacturer:'Bambu Lab',archived_at:null}))
    storeImage.mockRejectedValueOnce(new Error('Keine eindeutige Farbnummer'))
    await state.fillStoreImages()
    expect(storeImage).toHaveBeenCalledTimes(2)
    expect(state.imageIssues.value[0]).toContain('FIL-a')
    expect(state.items.value.find((v: FilamentSpool)=>v.id==='b').image_url).toBe('/local-image.png')
  })
  it('loads all inventory pages',async () => {
    const fetch=vi.fn().mockResolvedValueOnce({ok:true,status:200,json:async () => ({items:[{id:'a'}],has_more:true,next_offset:1})}).mockResolvedValueOnce({ok:true,status:200,json:async () => ({items:[{id:'b'}],has_more:false,next_offset:null})})
    vi.stubGlobal('fetch',fetch)
    try { expect((await filamentApi.list()).map(v => v.id)).toEqual(['a','b']); expect(fetch.mock.calls[1][0]).toContain('offset=1') }
    finally { vi.unstubAllGlobals() }
  })
})
