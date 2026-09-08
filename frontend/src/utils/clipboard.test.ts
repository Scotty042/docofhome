import { afterEach, describe, expect, it, vi } from 'vitest'
import { copyText } from './clipboard'

afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals() })

describe('copyText', () => {
  it('uses the Clipboard API when available', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined)
    vi.stubGlobal('navigator', { clipboard: { writeText } })
    await copyText('hello')
    expect(writeText).toHaveBeenCalledWith('hello')
  })

  it('falls back to execCommand when Clipboard API fails', async () => {
    vi.stubGlobal('navigator', { clipboard: { writeText: vi.fn().mockRejectedValue(new Error()) } })
    const execCommand = vi.fn().mockReturnValue(true)
    const field = { value: '', style: {}, setAttribute: vi.fn(), focus: vi.fn(), select: vi.fn(), remove: vi.fn() }
    vi.stubGlobal('document', { createElement: vi.fn().mockReturnValue(field), body: { appendChild: vi.fn() }, execCommand })
    await copyText('fallback')
    expect(execCommand).toHaveBeenCalledWith('copy')
    expect(field.value).toBe('fallback')
    expect(field.select).toHaveBeenCalledOnce()
    expect(field.remove).toHaveBeenCalledOnce()
    execCommand.mockReturnValue(false)
    await expect(copyText('rejected')).rejects.toThrow('Copy command was rejected')
    expect(field.remove).toHaveBeenCalledTimes(2)
  })
})
