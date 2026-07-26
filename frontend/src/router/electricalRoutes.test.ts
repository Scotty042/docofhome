import { describe, expect, it } from 'vitest'

import { electricalRoutes } from './electricalRoutes'

describe('electrical routes', () => {
  it('keeps static create, edit and layout routes ahead of distribution detail', () => {
    expect(electricalRoutes.map((route) => [route.path, route.name])).toEqual([
      ['/electrical', 'electrical'],
      ['/electrical/topology', 'electrical-topology'],
      ['/electrical/distributions/new', 'electrical-distribution-create'],
      ['/electrical/distributions/:id/edit', 'electrical-distribution-edit'],
      ['/electrical/distributions/:id/layout', 'electrical-distribution-layout'],
      ['/electrical/distributions/:id', 'electrical-distribution-detail'],
      ['/electrical/circuits/new', 'electrical-circuit-create'],
      ['/electrical/circuits/:id/edit', 'electrical-circuit-edit'],
      ['/electrical/circuits/:id', 'electrical-circuit-detail'],
      ['/electrical/protective-devices/new', 'electrical-protective-device-create'],
      ['/electrical/protective-devices/:id/edit', 'electrical-protective-device-edit']
    ])
  })
})
