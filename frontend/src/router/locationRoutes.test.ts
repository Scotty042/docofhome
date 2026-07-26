import { describe, expect, it } from 'vitest'

import { locationRoutes } from './locationRoutes'

describe('location routes', () => {
  it('keeps static create and edit routes ahead of the detail matcher', () => {
    expect(locationRoutes.map((route) => [route.path, route.name])).toEqual([
      ['/locations', 'locations'],
      ['/locations/setup', 'location-structure-wizard'],
      ['/locations/new', 'location-create'],
      ['/locations/:id/edit', 'location-edit'],
      ['/locations/:id', 'location-detail']
    ])
  })
})
