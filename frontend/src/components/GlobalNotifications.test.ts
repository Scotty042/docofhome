import source from './GlobalNotifications.vue?raw'
import { describe, expect, it } from 'vitest'

describe('global notification overlay contract', () => {
  it('renders above dialogs at the top and can be closed manually', () => {
    expect(source).toContain('location="top center"')
    expect(source).toContain('z-index: 10000 !important')
    expect(source).toContain('@click="notifications.dismissCurrent"')
  })
})
