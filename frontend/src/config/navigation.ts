import type { ModuleKey } from '../types/settings'

export interface NavigationItem { key: ModuleKey; title: string; icon: string; to: string }
export interface NavigationGroup { key: string; title: string; icon: string; items: NavigationItem[] }
export const navigationGroups: NavigationGroup[] = [
  { key: 'home', title: 'Zuhause', icon: 'mdi-home-outline', items: [
    { key: 'assets', title: 'Inventar', icon: 'mdi-package-variant-closed', to: '/assets' },
    { key: 'locations', title: 'Bereiche & Räume', icon: 'mdi-floor-plan', to: '/locations' }
  ] },
  { key: 'technology', title: 'Technik', icon: 'mdi-wrench-outline', items: [
    { key: 'electrical', title: 'Elektro', icon: 'mdi-flash-outline', to: '/electrical' },
    { key: 'network', title: 'Netzwerk', icon: 'mdi-lan', to: '/network' },
    { key: 'smart_home', title: 'Smart Home', icon: 'mdi-home-assistant', to: '/smart-home' },
    { key: 'workloads', title: 'Dienste & Container', icon: 'mdi-docker', to: '/workloads' }
  ] },
  { key: 'daily', title: 'Alltag', icon: 'mdi-chart-bar', items: [
    { key: 'consumption', title: 'Verbrauch', icon: 'mdi-lightning-bolt-outline', to: '/consumption' },
    { key: 'maintenance', title: 'Wartung & Aufgaben', icon: 'mdi-checkbox-marked-outline', to: '/maintenance' }
  ] },
  { key: 'collections', title: 'Sammlungen', icon: 'mdi-database-outline', items: [
    { key: 'filament', title: 'Filament-Sammlung', icon: 'mdi-printer-3d-nozzle-outline', to: '/filament' },
    { key: 'lego', title: 'LEGO-Sammlung', icon: 'mdi-toy-brick-outline', to: '/lego' }
  ] },
  { key: 'knowledge', title: 'Wissen', icon: 'mdi-book-open-page-variant-outline', items: [
    { key: 'wiki', title: 'Wiki-Seiten', icon: 'mdi-book-outline', to: '/wiki' },
    { key: 'documents', title: 'Dokumente', icon: 'mdi-file-document-outline', to: '/documents' },
    { key: 'images', title: 'Bilder', icon: 'mdi-image-multiple-outline', to: '/images' },
    { key: 'cookbook', title: 'Kochbuch', icon: 'mdi-chef-hat', to: '/wiki/kochbuch' }
  ] },
  { key: 'management', title: 'Verwaltung', icon: 'mdi-database-cog-outline', items: [
    { key: 'master_data', title: 'Stammdaten', icon: 'mdi-database-cog-outline', to: '/master-data' },
    { key: 'quality', title: 'Dokumentationsqualität', icon: 'mdi-clipboard-check-outline', to: '/quality' }
  ] }
]

export function enabledNavigation(enabled: readonly ModuleKey[]): NavigationGroup[] {
  const active = new Set(enabled)
  return navigationGroups.map(group => ({ ...group, items: group.items.filter(item => active.has(item.key)) }))
    .filter(group => group.items.length > 0)
}

export function navigationGroupForPath(path: string): string | undefined {
  // Prefer the most specific domain route over a shorter parent path.
  return navigationGroups.flatMap(group => group.items.map(item => ({ group: group.key, path: item.to })))
    .filter(item => path === item.path || path.startsWith(`${item.path}/`))
    .sort((a, b) => b.path.length - a.path.length)[0]?.group
}
