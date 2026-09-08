import source from './GlobalNotifications.vue?raw'
import { describe, expect, it } from 'vitest'

describe('global notification overlay contract', () => {
  it('renders above dialogs at the top and can be closed manually', () => {
    expect(source).toContain('<Teleport to="body">')
    expect(source).toContain('z-index: 32000')
    expect(source).toContain('left: 50%')
    expect(source).toContain('top: max(12px, env(safe-area-inset-top))')
    expect(source).toContain('@click:close="notifications.dismiss(item.id)"')
  })
})
