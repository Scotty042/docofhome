import { nextTick } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { isGlobalSearchShortcut, useGlobalSearch } from './useGlobalSearch'
import type { SearchResponse } from '../types/search'

function result(query: string, title: string): SearchResponse {
  return {
    query,
    total: 1,
    groups: [
      {
        result_type: 'asset',
        label: 'Assets',
        total: 1,
        results: [
          {
            result_type: 'asset',
            id: title,
            title,
            subtitle: 'A-001',
            description: null,
            route: `/assets/${title}`,
            archived: false,
            matched_fields: ['Name']
          }
        ]
      }
    ]
  }
}

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

afterEach(() => {
  vi.useRealTimers()
})

describe('global search state', () => {
  it('does not request fewer than two visible characters and debounces valid input', async () => {
    vi.useFakeTimers()
    const request = vi.fn().mockResolvedValue(result('ab', 'Treffer'))
    const search = useGlobalSearch({ debounceMs: 250, request })

    search.query.value = ' a '
    await nextTick()
    await vi.advanceTimersByTimeAsync(500)
    expect(request).not.toHaveBeenCalled()

    search.query.value = ' ab '
    await nextTick()
    await vi.advanceTimersByTimeAsync(249)
    expect(request).not.toHaveBeenCalled()
    await vi.advanceTimersByTimeAsync(1)
    await nextTick()

    expect(request).toHaveBeenCalledTimes(1)
    expect(request.mock.calls[0]?.[0]).toBe('ab')
    expect(search.response.value?.query).toBe('ab')
    search.dispose()
  })

  it('does not allow an older response to overwrite a newer query', async () => {
    vi.useFakeTimers()
    const first = deferred<SearchResponse>()
    const second = deferred<SearchResponse>()
    const request = vi.fn()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise)
    const search = useGlobalSearch({ debounceMs: 10, request })

    search.query.value = 'ab'
    await nextTick()
    await vi.advanceTimersByTimeAsync(10)
    search.query.value = 'abc'
    await nextTick()
    await vi.advanceTimersByTimeAsync(10)

    second.resolve(result('abc', 'Neu'))
    await Promise.resolve()
    await nextTick()
    first.resolve(result('ab', 'Alt'))
    await Promise.resolve()
    await nextTick()

    expect(search.response.value?.query).toBe('abc')
    expect(search.flatResults.value[0]?.title).toBe('Neu')
    search.dispose()
  })

  it('cycles keyboard selection through the flattened result list', async () => {
    vi.useFakeTimers()
    const twoResults = result('ab', 'Erster')
    twoResults.total = 2
    twoResults.groups[0]?.results.push({
      ...twoResults.groups[0].results[0]!,
      id: 'second',
      title: 'Zweiter',
      route: '/assets/second'
    })
    twoResults.groups[0]!.total = 2
    const search = useGlobalSearch({
      debounceMs: 1,
      request: vi.fn().mockResolvedValue(twoResults)
    })

    search.query.value = 'ab'
    await nextTick()
    await vi.advanceTimersByTimeAsync(1)
    await nextTick()
    expect(search.activeIndex.value).toBe(0)
    search.moveActive(1)
    expect(search.activeIndex.value).toBe(1)
    search.moveActive(1)
    expect(search.activeIndex.value).toBe(0)
    search.moveActive(-1)
    expect(search.activeIndex.value).toBe(1)
    search.dispose()
  })
})

describe('global search shortcut', () => {
  it('accepts Ctrl+K, Cmd+K and slash but not Alt+K', () => {
    expect(isGlobalSearchShortcut({ key: 'k', ctrlKey: true, metaKey: false, altKey: false })).toBe(true)
    expect(isGlobalSearchShortcut({ key: 'K', ctrlKey: false, metaKey: true, altKey: false })).toBe(true)
    expect(isGlobalSearchShortcut({ key: 'k', ctrlKey: true, metaKey: false, altKey: true })).toBe(false)
    expect(isGlobalSearchShortcut({ key: '/', ctrlKey: false, metaKey: false, altKey: false })).toBe(true)
    expect(isGlobalSearchShortcut({ key: '/', ctrlKey: true, metaKey: false, altKey: false })).toBe(false)
    expect(isGlobalSearchShortcut({ key: 'f', ctrlKey: true, metaKey: false, altKey: false })).toBe(false)
  })
})
