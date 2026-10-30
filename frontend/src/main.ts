import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'
import './styles/main.css'

import { createApp } from 'vue'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import { aliases, mdi } from 'vuetify/iconsets/mdi'

import App from './App.vue'
import { pinia } from './pinia'
import router from './router'

const vuetify = createVuetify({
  defaults: {
    VBtn: { elevation: 0, height: 36 },
    VTextField: { variant: 'outlined', density: 'compact', color: 'primary' },
    VSelect: { variant: 'outlined', density: 'compact', color: 'primary' },
    VAutocomplete: { variant: 'outlined', density: 'compact', color: 'primary' },
    VTextarea: { variant: 'outlined', color: 'primary' },
    VRow: { dense: true },
    VList: { density: 'compact' },
    VTable: { density: 'compact' },
    VTabs: { height: 40 },
    VSwitch: { density: 'compact' },
    VCheckbox: { density: 'compact' },
    VCard: { elevation: 0, rounded: 'lg' },
    VTooltip: { openDelay: 350 }
  },
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi }
  },
  theme: {
    defaultTheme: 'jarvisLight',
    themes: {
      jarvisDark: {
        dark: true,
        colors: {
          background: '#18221c',
          'on-background': '#edf3e9',
          'on-surface': '#edf3e9',
          'on-primary': '#193420',
          'surface-variant': '#334b38',
          'on-surface-variant': '#e1eed9',
          surface: '#202e25',
          primary: '#a8cfa7',
          secondary: '#b5c4b5',
          success: '#a6c98b',
          warning: '#eab67d',
          error: '#ef9c91',
          info: '#a5cbd1'
        }
      },
      jarvisLight: {
        dark: false,
        colors: {
          background: '#f8f7f3',
          'on-background': '#152b2b',
          'on-surface': '#152b2b',
          'on-primary': '#ffffff',
          'surface-variant': '#e7ede4',
          'on-surface-variant': '#315542',
          surface: '#ffffff',
          primary: '#2d6054',
          secondary: '#63736b',
          success: '#477035',
          warning: '#a55c22',
          error: '#b44035',
          info: '#436b80'
        }
      }
    }
  }
})

createApp(App).use(pinia).use(router).use(vuetify).mount('#app')

if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/service-worker.js'))
}
