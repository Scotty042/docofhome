import { describe, expect, it } from 'vitest'
import { enabledNavigation, navigationGroupForPath, navigationGroups } from './navigation'
import { moduleKeys } from '../types/settings'

describe('grouped application navigation', () => {
  it('keeps every enabled domain reachable exactly once', () => {
    const items = enabledNavigation(moduleKeys).flatMap(group => group.items)
    expect(new Set(items.map(item => item.key)).size).toBe(moduleKeys.length)
    expect(items.map(item => item.key).sort()).toEqual([...moduleKeys].sort())
  })
  it('removes disabled modules and empty groups without losing collection routes', () => {
    const groups = enabledNavigation(['assets', 'filament', 'lego'])
    expect(groups.map(group => group.key)).toEqual(['home', 'collections'])
    expect(groups.flatMap(group => group.items).map(item => item.to)).toEqual(['/assets', '/filament', '/lego'])
    expect(navigationGroups.length).toBe(6)
  })
  it('opens the domain on nested routes and does not match similarly named prefixes', () => {
    expect(navigationGroupForPath('/assets/123/edit')).toBe('home')
    expect(navigationGroupForPath('/filament/123')).toBe('collections')
    expect(navigationGroupForPath('/wiki/kochbuch')).toBe('knowledge')
    expect(navigationGroupForPath('/assets-other')).toBeUndefined()
  })
})
