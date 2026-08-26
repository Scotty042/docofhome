import { createRouter, createWebHistory } from 'vue-router'
import { pinia } from '../pinia'
import AboutPage from '../pages/AboutPage.vue'
import ArchivePage from '../pages/ArchivePage.vue'
import AssetDetailPage from '../pages/AssetDetailPage.vue'
import AssetEditorPage from '../pages/AssetEditorPage.vue'
import AssetListPage from '../pages/AssetListPage.vue'
import BackupPage from '../pages/BackupPage.vue'
import DashboardPage from '../pages/DashboardPage.vue'
import DataManagementPage from '../pages/DataManagementPage.vue'
import DocumentsPage from '../pages/DocumentsPage.vue'
import ConsumptionPage from '../pages/ConsumptionPage.vue'
import CookbookPage from '../pages/CookbookPage.vue'
import ImmichGalleryPage from '../pages/ImmichGalleryPage.vue'
import GuidedSetupPage from '../pages/GuidedSetupPage.vue'
import MasterDataPage from '../pages/MasterDataPage.vue'
import MaintenancePage from '../pages/MaintenancePage.vue'
import NetworkDeviceDetailPage from '../pages/NetworkDeviceDetailPage.vue'
import NetworkPage from '../pages/NetworkPage.vue'
import QualityPage from '../pages/QualityPage.vue'
import SettingsPage from '../pages/SettingsPage.vue'
import ServiceUnavailablePage from '../pages/ServiceUnavailablePage.vue'
import SetupWizardPage from '../pages/SetupWizardPage.vue'
import SmartHomePage from '../pages/SmartHomePage.vue'
import WikiPage from '../pages/WikiPage.vue'
import WorkloadsPage from '../pages/WorkloadsPage.vue'
import { useSettingsStore } from '../stores/settings'
import { electricalRoutes } from './electricalRoutes'
import { handbookRoutes } from './handbookRoutes'
import { locationRoutes } from './locationRoutes'
import { resolveSetupNavigation } from './setupNavigation'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardPage },
    ...locationRoutes,
    ...electricalRoutes,
    { path: '/assets', name: 'assets', component: AssetListPage },
    { path: '/assets/new', name: 'asset-create', component: AssetEditorPage },
    { path: '/assets/:id/replace', name: 'asset-replace', component: AssetEditorPage },
    { path: '/assets/:id/edit', name: 'asset-edit', component: AssetEditorPage },
    { path: '/assets/:id', name: 'asset-detail', component: AssetDetailPage },
    { path: '/master-data', name: 'master-data', component: MasterDataPage },
    { path: '/smart-home', name: 'smart-home', component: SmartHomePage },
    { path: '/images', name: 'images', component: ImmichGalleryPage },
    { path: '/documents', name: 'documents', component: DocumentsPage },
    { path: '/consumption', name: 'consumption', component: ConsumptionPage },
    ...handbookRoutes,
    { path: '/wiki', name: 'wiki', component: WikiPage },
    { path: '/wiki/kochbuch', name: 'cookbook', component: CookbookPage },
    { path: '/maintenance', name: 'maintenance', component: MaintenancePage },
    { path: '/network', name: 'network', component: NetworkPage },
    { path: '/workloads', name: 'workloads', component: WorkloadsPage },
    { path: '/network/devices/:id', name: 'network-device-detail', component: NetworkDeviceDetailPage },
    { path: '/quality', name: 'quality', component: QualityPage },
    { path: '/data-management', name: 'data-management', component: DataManagementPage },
    { path: '/guided-setup', name: 'guided-setup', component: GuidedSetupPage },
    { path: '/archive', name: 'archive', component: ArchivePage },
    { path: '/about', name: 'about', component: AboutPage },
    { path: '/backups', name: 'backups', component: BackupPage },
    { path: '/setup', name: 'setup', component: SetupWizardPage, meta: { setupLayout: true } },
    {
      path: '/unavailable',
      name: 'unavailable',
      component: ServiceUnavailablePage,
      meta: { setupLayout: true }
    },
    { path: '/settings', name: 'settings', component: SettingsPage }
  ]
})

router.beforeEach(async (to) => {
  const settings = useSettingsStore(pinia)
  try {
    const completed = await settings.fetchSetupStatus()
    const setupRedirect = resolveSetupNavigation(String(to.name ?? ''), to.fullPath, completed)
    if (setupRedirect !== true) return setupRedirect
    if (!settings.configuration) await settings.fetchConfiguration()
    const routeModules: Array<[string, string]> = [
      ['/locations', 'locations'], ['/electrical', 'electrical'], ['/assets', 'assets'],
      ['/master-data', 'master_data'], ['/network', 'network'], ['/smart-home', 'smart_home'],
      ['/consumption', 'consumption'], ['/maintenance', 'maintenance'], ['/quality', 'quality'],
      ['/wiki/kochbuch', 'cookbook'], ['/wiki', 'wiki']
    ]
    const required = routeModules.find(([prefix]) => to.path.startsWith(prefix))?.[1]
    if (required && !(settings.configuration?.enabled_modules ?? []).includes(required as never)) return '/'
    return true
  } catch {
    return resolveSetupNavigation(String(to.name ?? ''), to.fullPath, 'unavailable')
  }
})

export default router
