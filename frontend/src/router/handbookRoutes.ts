import type { RouteRecordRaw } from 'vue-router'

import HandbookGlossaryPage from '../pages/HandbookGlossaryPage.vue'

export const handbookRoutes: RouteRecordRaw[] = [
  {
    path: '/wiki/handbuch',
    name: 'wiki-handbook',
    component: HandbookGlossaryPage
  }
]
