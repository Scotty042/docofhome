import { defineComponent, h, onMounted, ref, type VNode } from 'vue'

import { APP_SUPPORT_LABEL } from '../config/branding'
import { settingsApi } from '../services/settingsApi'

export const SUPPORT_URL = 'https://buymeacoffee.com/scotty42'

export function renderSupportFooter(version = 'Version wird geladen'): VNode {
  return h('footer', { class: 'app-support-footer', 'aria-label': 'Anwendungsinformationen' }, [
    h('span', { class: 'app-version' }, version),
    h('span', { class: 'app-footer-separator', 'aria-hidden': 'true' }, '·'),
    h('a', {
      class: 'app-support-link',
      href: SUPPORT_URL,
      target: '_blank',
      rel: 'noopener noreferrer'
    }, APP_SUPPORT_LABEL)
  ])
}

export default defineComponent({
  name: 'SupportFooter',
  setup() {
    const version = ref('Version wird geladen')
    onMounted(async () => {
      try {
        const health = await settingsApi.health()
        version.value = `Version ${health.version}`
      } catch {
        version.value = 'Version nicht verfügbar'
      }
    })
    return () => renderSupportFooter(version.value)
  }
})
