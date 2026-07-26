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
  components,
  directives,
  icons: {
    defaultSet: 'mdi',
    aliases,
    sets: { mdi }
  },
  theme: {
    defaultTheme: 'jarvisDark',
    themes: {
      jarvisDark: {
        dark: true,
        colors: {
          background: '#0f1720',
          surface: '#17212b',
          primary: '#26c6da',
          secondary: '#90a4ae',
          success: '#66bb6a',
          warning: '#ffa726',
          error: '#ef5350',
          info: '#42a5f5'
        }
      },
      jarvisLight: {
        dark: false,
        colors: {
          background: '#f3f6f8',
          surface: '#ffffff',
          primary: '#007c91',
          secondary: '#546e7a',
          success: '#2e7d32',
          warning: '#ef6c00',
          error: '#c62828',
          info: '#1565c0'
        }
      }
    }
  }
})

createApp(App).use(pinia).use(router).use(vuetify).mount('#app')
