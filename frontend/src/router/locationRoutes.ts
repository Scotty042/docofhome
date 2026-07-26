import type { RouteRecordRaw } from 'vue-router'

import LocationDetailPage from '../pages/LocationDetailPage.vue'
import LocationEditorPage from '../pages/LocationEditorPage.vue'
import LocationListPage from '../pages/LocationListPage.vue'
import BuildingStructureWizardPage from '../pages/BuildingStructureWizardPage.vue'

export const locationRoutes: RouteRecordRaw[] = [
  { path: '/locations', name: 'locations', component: LocationListPage },
  { path: '/locations/setup', name: 'location-structure-wizard', component: BuildingStructureWizardPage },
  { path: '/locations/new', name: 'location-create', component: LocationEditorPage },
  { path: '/locations/:id/edit', name: 'location-edit', component: LocationEditorPage },
  { path: '/locations/:id', name: 'location-detail', component: LocationDetailPage }
]
