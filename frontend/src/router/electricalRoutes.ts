import type { RouteRecordRaw } from 'vue-router'

import ElectricalDistributionDetailPage from '../pages/ElectricalDistributionDetailPage.vue'
import ElectricalCircuitEditorPage from '../pages/ElectricalCircuitEditorPage.vue'
import ElectricalCircuitDetailPage from '../pages/ElectricalCircuitDetailPage.vue'
import ElectricalDistributionEditorPage from '../pages/ElectricalDistributionEditorPage.vue'
import ElectricalDistributionLayoutPage from '../pages/ElectricalDistributionLayoutPage.vue'
import ElectricalListPage from '../pages/ElectricalListPage.vue'
import ElectricalProtectiveDeviceEditorPage from '../pages/ElectricalProtectiveDeviceEditorPage.vue'
import ElectricalTopologyPage from '../pages/ElectricalTopologyPage.vue'

export const electricalRoutes: RouteRecordRaw[] = [
  { path: '/electrical', name: 'electrical', component: ElectricalListPage },
  {
    path: '/electrical/topology',
    name: 'electrical-topology',
    component: ElectricalTopologyPage
  },
  {
    path: '/electrical/distributions/new',
    name: 'electrical-distribution-create',
    component: ElectricalDistributionEditorPage
  },
  {
    path: '/electrical/distributions/:id/edit',
    name: 'electrical-distribution-edit',
    component: ElectricalDistributionEditorPage
  },
  {
    path: '/electrical/distributions/:id/layout',
    name: 'electrical-distribution-layout',
    component: ElectricalDistributionLayoutPage
  },
  {
    path: '/electrical/distributions/:id',
    name: 'electrical-distribution-detail',
    component: ElectricalDistributionDetailPage
  },
  {
    path: '/electrical/circuits/new',
    name: 'electrical-circuit-create',
    component: ElectricalCircuitEditorPage
  },
  {
    path: '/electrical/circuits/:id/edit',
    name: 'electrical-circuit-edit',
    component: ElectricalCircuitEditorPage
  },
  {
    path: '/electrical/circuits/:id',
    name: 'electrical-circuit-detail',
    component: ElectricalCircuitDetailPage
  },
  {
    path: '/electrical/protective-devices/new',
    name: 'electrical-protective-device-create',
    component: ElectricalProtectiveDeviceEditorPage
  },
  {
    path: '/electrical/protective-devices/:id/edit',
    name: 'electrical-protective-device-edit',
    component: ElectricalProtectiveDeviceEditorPage
  }
]
