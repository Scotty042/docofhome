import { describe, expect, it } from 'vitest'
import type { VNode } from 'vue'

import { APP_SUPPORT_LABEL } from '../config/branding'
import { renderSupportFooter, SUPPORT_URL } from './SupportFooter'

describe('support footer', () => {
  it('renders the secure Buy Me a Coffee link in a new tab', () => {
    const footer = renderSupportFooter()
    const children = footer.children as VNode[]
    const link = children.find((child) => child.type === 'a')

    expect(footer.type).toBe('footer')
    expect(link).toBeDefined()
    expect(link?.children).toBe(APP_SUPPORT_LABEL)
    expect(link?.props).toMatchObject({
      href: SUPPORT_URL,
      target: '_blank',
      rel: 'noopener noreferrer'
    })
    expect(SUPPORT_URL).toBe('https://buymeacoffee.com/scotty42')
  })
})
