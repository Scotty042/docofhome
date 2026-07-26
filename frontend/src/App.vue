<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDisplay, useTheme } from 'vuetify'

import GlobalNotifications from './components/GlobalNotifications.vue'
import GlobalSearch from './components/GlobalSearch.vue'
import SupportFooter from './components/SupportFooter'
import { APP_NAME, APP_SLOGAN } from './config/branding'
import { useSettingsStore } from './stores/settings'
import { moduleKeys, type ModuleKey } from './types/settings'

interface ModuleNavigationItem {
  key: ModuleKey
  title: string
  icon: string
  to?: string
  disabled?: boolean
}

const route = useRoute()
const settings = useSettingsStore()
const theme = useTheme()
const { mdAndUp } = useDisplay()
const drawerOpen = ref(mdAndUp.value)
const drawerPermanent = computed(() => mdAndUp.value)
const moreRoutes = ['/guided-setup', '/backups', '/data-management', '/archive', '/settings', '/about']
const openNavigationGroups = ref<string[]>(
  ['wiki', 'more'].filter((group) => sessionStorage.getItem(`docofhome.navigation.${group}`) === 'open')
)
function setNavigationGroup(group: string, open: boolean) {
  const groups = new Set(openNavigationGroups.value)
  if (open) groups.add(group)
  else groups.delete(group)
  openNavigationGroups.value = [...groups]
}
const moreOpen = computed({
  get: () => openNavigationGroups.value.includes('more'),
  set: (open: boolean) => setNavigationGroup('more', open)
})
const setupLayout = computed(() => route.meta.setupLayout === true)
const installationName = computed(() => settings.configuration?.installation_name ?? APP_NAME)
const moduleNavigation: ModuleNavigationItem[] = [
  { key: 'locations', title: 'Bereiche & Räume', icon: 'mdi-home-floor-0', to: '/locations' },
  { key: 'electrical', title: 'Elektro', icon: 'mdi-flash', to: '/electrical' },
  { key: 'assets', title: 'Assets', icon: 'mdi-devices', to: '/assets' },
  { key: 'master_data', title: 'Stammdaten', icon: 'mdi-database-cog-outline', to: '/master-data' },
  { key: 'network', title: 'Netzwerk', icon: 'mdi-lan', to: '/network' },
  { key: 'smart_home', title: 'Smart Home', icon: 'mdi-home-assistant', to: '/smart-home' },
  { key: 'consumption', title: 'Verbrauch', icon: 'mdi-chart-line', to: '/consumption' },
  { key: 'maintenance', title: 'Wartung & Aufgaben', icon: 'mdi-format-list-checks', to: '/maintenance' },
  { key: 'quality', title: 'Dokumentationsqualität', icon: 'mdi-clipboard-check-outline', to: '/quality' }
]
const enabledModules = computed(() => new Set(settings.configuration?.enabled_modules ?? moduleKeys))
const visibleModuleNavigation = computed(() => (
  moduleNavigation.filter((item) => enabledModules.value.has(item.key))
))
const wikiEnabled = computed(() => enabledModules.value.has('wiki'))

watch(mdAndUp, (isDesktop) => {
  drawerOpen.value = isDesktop
})

watch(openNavigationGroups, (groups) => {
  for (const group of ['wiki', 'more']) {
    sessionStorage.setItem(
      `docofhome.navigation.${group}`,
      groups.includes(group) ? 'open' : 'closed'
    )
  }
}, { deep: true })

watch(
  () => route.path,
  (path) => {
    if (moreRoutes.some((entry) => path.startsWith(entry))) moreOpen.value = true
    if (path.startsWith('/wiki')) setNavigationGroup('wiki', true)
  },
  { immediate: true }
)

watch(
  () => settings.configuration?.theme,
  (preference) => {
    theme.global.name.value = preference === 'light' ? 'jarvisLight' : 'jarvisDark'
  },
  { immediate: true }
)

onMounted(async () => {
  if (settings.setupComplete && !settings.configuration) {
    try {
      await settings.fetchConfiguration()
    } catch {
      // The page-level alert presents the API error without exposing request data.
    }
  }
})
</script>

<template>
  <v-app>
    <GlobalNotifications />
    <template v-if="!setupLayout">
      <v-app-bar flat border>
        <v-app-bar-nav-icon
          v-if="!drawerPermanent"
          aria-label="Navigation öffnen"
          title="Navigation öffnen"
          @click="drawerOpen = !drawerOpen"
        />
        <v-app-bar-title class="app-title">
          <strong>{{ installationName }}</strong>
          <span class="slogan">{{ APP_NAME }} · {{ APP_SLOGAN }}</span>
        </v-app-bar-title>
        <GlobalSearch />
        <v-chip
          class="mr-3 d-none d-sm-flex"
          color="success"
          variant="tonal"
          prepend-icon="mdi-server-network"
        >
          System bereit
        </v-chip>
      </v-app-bar>

      <v-navigation-drawer v-model="drawerOpen" :permanent="drawerPermanent">
        <v-list v-model:opened="openNavigationGroups" nav>
          <v-list-item prepend-icon="mdi-view-dashboard" title="Dashboard" to="/" />
          <v-list-item
            v-for="item in visibleModuleNavigation"
            :key="item.key"
            :prepend-icon="item.icon"
            :title="item.title"
            :to="item.to"
            :disabled="item.disabled"
          />
          <v-list-group v-if="wikiEnabled" value="wiki">
            <template #activator="{ props }">
              <v-list-item v-bind="props" prepend-icon="mdi-book-open-page-variant" title="Wiki" />
            </template>
            <v-list-item prepend-icon="mdi-file-document-outline" title="Wiki-Seiten" to="/wiki" />
            <v-list-item prepend-icon="mdi-format-list-bulleted" title="Handbuch & Glossar" to="/wiki/handbuch" />
          </v-list-group>
          <v-list-item prepend-icon="mdi-image-multiple-outline" title="Bilder" to="/images" />
          <v-list-item prepend-icon="mdi-folder-outline" title="Dokumente" to="/documents" />
          <v-list-item prepend-icon="mdi-docker" title="Dienste & Container" to="/workloads" />
          <v-list-group value="more">
            <template #activator="{ props }">
              <v-list-item v-bind="props" prepend-icon="mdi-menu" title="Mehr" />
            </template>
            <v-list-item prepend-icon="mdi-wizard-hat" title="Geführte Einrichtung" to="/guided-setup" />
            <v-list-item prepend-icon="mdi-database-arrow-up-outline" title="Backup" to="/backups" />
            <v-list-item prepend-icon="mdi-database-sync-outline" title="Daten & Historie" to="/data-management" />
            <v-list-item prepend-icon="mdi-archive-outline" title="Archiv" to="/archive" />
            <v-list-item prepend-icon="mdi-cog" title="Einstellungen" to="/settings" />
            <v-list-item prepend-icon="mdi-information-outline" title="Über DocOfHome" to="/about" />
          </v-list-group>
        </v-list>
      </v-navigation-drawer>
    </template>

    <v-main>
      <v-alert
        v-if="settings.error && !setupLayout"
        type="error"
        variant="tonal"
        class="ma-4"
        closable
      >
        {{ settings.error }}
      </v-alert>
      <router-view />
    </v-main>
    <SupportFooter v-if="!setupLayout" />
  </v-app>
</template>

<style scoped>
.app-title {
  min-width: 180px;
}

.slogan {
  margin-left: 0.75rem;
  color: rgb(var(--v-theme-secondary));
  font-size: 0.85rem;
  font-weight: 400;
}

@media (max-width: 500px) {
  .slogan {
    display: none;
  }
}
</style>
