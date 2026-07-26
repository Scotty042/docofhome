import appSource from '../App.vue?raw'
import handbookSource from './HandbookGlossaryPage.vue?raw'
import layoutSource from './ElectricalDistributionLayoutPage.vue?raw'
import wikiSource from './WikiPage.vue?raw'
import { describe, expect, it } from 'vitest'

import { handbookRoutes } from '../router/handbookRoutes'

describe('handbook route, navigation and mobile structure', () => {
  it('adds a dedicated static route below Wiki while preserving editable Wiki pages', () => {
    expect(handbookRoutes.map((route) => [route.path, route.name])).toEqual([
      ['/wiki/handbuch', 'wiki-handbook']
    ])
    expect(appSource).toContain('title="Wiki-Seiten" to="/wiki"')
    expect(appSource).toContain('title="Handbuch & Glossar" to="/wiki/handbuch"')
    expect(wikiSource).toContain('knowledgeApi.wikiPages')
    expect(wikiSource).toContain('Neue Hauptseite')
  })

  it('contains search, category filtering, glossary mode, anchors and responsive navigation', () => {
    expect(handbookSource).toContain('Handbuch und Glossar durchsuchen')
    expect(handbookSource).toContain('selectedCategory')
    expect(handbookSource).toContain('Glossar A–Z')
    expect(handbookSource).toContain('Sprungmarken')
    expect(handbookSource).toContain('entryAnchor(entry)')
    expect(handbookSource).toContain('d-md-none')
    expect(handbookSource).toContain('d-none d-md-block')
    expect(handbookSource).toContain('Änderungen an elektrischen Anlagen gehören in die Hände einer Elektrofachkraft')
    expect(handbookSource).not.toContain('knowledgeApi')
  })

  it('shows Asset bearbeiten only for DIN entries backed by an asset', () => {
    expect(layoutSource).toContain('`/assets/${detailDevice.asset.id}/edit`">Asset bearbeiten')
    expect(layoutSource).toContain('`/assets/${detailAsset.asset_id}/edit`">Asset bearbeiten')
    const passiveBlock = layoutSource.slice(
      layoutSource.indexOf('<template v-else-if="detailComponent">'),
      layoutSource.indexOf('<template v-else-if="detailAsset">')
    )
    expect(passiveBlock).not.toContain('Asset bearbeiten')
    expect(layoutSource).toContain('Position bearbeiten')
  })
})
