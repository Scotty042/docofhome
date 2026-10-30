<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDisplay, useTheme } from 'vuetify'
import GlobalNotifications from './components/GlobalNotifications.vue'
import GlobalSearch from './components/GlobalSearch.vue'
import SupportFooter from './components/SupportFooter'
import { APP_NAME, APP_SLOGAN } from './config/branding'
import { enabledNavigation, navigationGroupForPath } from './config/navigation'
import { useSettingsStore } from './stores/settings'
import { moduleKeys } from './types/settings'

const route = useRoute()
const settings = useSettingsStore()
const theme = useTheme()
const { mdAndUp } = useDisplay()
const drawerOpen = ref(mdAndUp.value)
const setupLayout = computed(() => route.meta.setupLayout === true)
const installationName = computed(() => settings.configuration?.installation_name || APP_NAME)
const enabledModules = computed(() => settings.configuration?.enabled_modules ?? moduleKeys)
const groups = computed(() => enabledNavigation(enabledModules.value))
const shortcuts = computed(() => {
  const chosen = settings.configuration?.main_menu_modules ?? enabledModules.value
  if (chosen.length === enabledModules.value.length) return []
  return groups.value.flatMap(group => group.items).filter(item => chosen.includes(item.key))
})
function initialGroups(): string[] {
  try {
    const saved: unknown = JSON.parse(sessionStorage.getItem('docofhome.navigation.groups.v1.9.1') || 'null')
    if (Array.isArray(saved) && saved.every(value => typeof value === 'string')) return saved
  } catch { /* A denied or invalid storage entry must not block navigation. */ }
  return ['home', 'daily', 'collections']
}
const openGroups = ref<string[]>(initialGroups())
watch(openGroups, value => {
  try { sessionStorage.setItem('docofhome.navigation.groups.v1.9.1', JSON.stringify(value)) } catch { /* Optional session preference. */ }
}, { deep: true })
watch(mdAndUp, value => { drawerOpen.value = value })
watch(() => route.path, path => {
  const group = navigationGroupForPath(path)
  if (group && !openGroups.value.includes(group)) openGroups.value = [...openGroups.value, group]
  if (!mdAndUp.value) drawerOpen.value = false
}, { immediate: true })
watch(() => settings.configuration?.theme, preference => {
  theme.global.name.value = preference === 'dark' ? 'jarvisDark' : 'jarvisLight'
}, { immediate: true })
onMounted(async () => {
  if (settings.setupComplete && !settings.configuration) {
    try { await settings.fetchConfiguration() } catch { /* Error shown below. */ }
  }
})
</script>

<template>
  <v-app>
    <a class="skip-to-content" href="#main-content">Zum Inhalt</a>
    <GlobalNotifications />
    <template v-if="!setupLayout">
      <v-navigation-drawer v-model="drawerOpen" :permanent="mdAndUp" :temporary="!mdAndUp" :width="274" class="home-navigation">
        <router-link to="/" class="home-brand" :aria-label="`${APP_NAME} – Übersicht`">
          <span>Doc<em>Of</em>Home</span>
          <small>{{ installationName }}</small>
        </router-link>
        <v-list v-model:opened="openGroups" open-strategy="multiple" nav aria-label="Hauptnavigation" class="home-nav-list">
          <v-list-item prepend-icon="mdi-home-variant" title="Übersicht" to="/" exact class="overview-link" />
          <v-list-group v-if="shortcuts.length" value="shortcuts">
            <template #activator="{ props }"><v-list-item v-bind="props" title="Schnellzugriff" prepend-icon="mdi-star-outline" /></template>
            <v-list-item v-for="item in shortcuts" :key="item.key" :title="item.title" :to="item.to" :prepend-icon="item.icon" exact />
          </v-list-group>
          <v-list-group v-for="group in groups" :key="group.key" :value="group.key">
            <template #activator="{ props }"><v-list-item v-bind="props" :title="group.title" :prepend-icon="group.icon" /></template>
            <template v-for="item in group.items" :key="item.key">
              <v-list-item v-if="item.key === 'wiki'" prepend-icon="mdi-book-outline" title="Wiki-Seiten" to="/wiki" exact />
              <v-list-item v-else :title="item.title" :to="item.to" :prepend-icon="item.icon" />
            </template>
          </v-list-group>
          <v-list-group value="tools">
            <template #activator="{ props }"><v-list-item v-bind="props" title="Daten & Werkzeuge" prepend-icon="mdi-database-sync-outline" /></template>
            <v-list-item title="Geführte Einrichtung" to="/guided-setup" prepend-icon="mdi-wizard-hat" />
            <v-list-item title="Backup" to="/backups" prepend-icon="mdi-database-arrow-up-outline" />
            <v-list-item title="Daten & Historie" to="/data-management" prepend-icon="mdi-database-sync-outline" />
            <v-list-item title="Archiv" to="/archive" prepend-icon="mdi-archive-outline" />
          </v-list-group>
        </v-list>
        <template #append>
          <v-list nav class="home-nav-bottom">
            <v-list-item title="Einstellungen" to="/settings" prepend-icon="mdi-cog-outline" />
            <v-list-item v-if="enabledModules.includes('wiki')" title="Handbuch & Glossar" to="/wiki/handbuch" prepend-icon="mdi-help-circle-outline" />
            <v-list-item title="Über DocOfHome" to="/about" prepend-icon="mdi-information-outline" />
          </v-list>
          <p class="home-tagline">{{ APP_SLOGAN }}</p>
        </template>
      </v-navigation-drawer>
      <v-app-bar flat class="home-topbar" :height="72">
        <v-app-bar-nav-icon v-if="!mdAndUp" aria-label="Navigation öffnen" @click="drawerOpen = !drawerOpen" />
        <span v-if="!mdAndUp" class="mobile-brand">{{ APP_NAME }}</span>
        <GlobalSearch />
        <v-spacer />
        <v-btn icon="mdi-cog-outline" to="/settings" variant="text" aria-label="Einstellungen" />
        <span class="home-app-label d-none d-lg-flex">Deine digitale Hausakte</span>
      </v-app-bar>
    </template>
    <v-main id="main-content" tabindex="-1">
      <v-alert v-if="settings.error && !setupLayout" type="error" variant="tonal" class="ma-4" closable>{{ settings.error }}</v-alert>
      <router-view />
    </v-main>
    <SupportFooter v-if="!setupLayout" />
  </v-app>
</template>
