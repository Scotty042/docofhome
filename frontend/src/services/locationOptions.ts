import type { Location, LocationTreeNode } from '../types/locations'

function locationOrder(left: Location, right: Location): number {
  const leftOrder = left.sort_order ?? Number.MAX_SAFE_INTEGER
  const rightOrder = right.sort_order ?? Number.MAX_SAFE_INTEGER
  if (leftOrder !== rightOrder) return leftOrder - rightOrder
  return left.name.localeCompare(right.name, 'de', { sensitivity: 'base', numeric: true })
}

export function sortLocationTree(nodes: LocationTreeNode[]): LocationTreeNode[] {
  return [...nodes]
    .sort(locationOrder)
    .map((node) => ({ ...node, children: sortLocationTree(node.children ?? []) }))
}

export function flattenLocationTree(nodes: LocationTreeNode[]): Location[] {
  const result: Location[] = []
  const append = (items: LocationTreeNode[]) => {
    for (const item of sortLocationTree(items)) {
      result.push(item)
      append(item.children ?? [])
    }
  }
  append(nodes)
  return result
}

export type LocationSelectItem = {
  value: string
  title: string
  depth: number
  location: LocationTreeNode
}

export function locationSelectItems(nodes: LocationTreeNode[]): LocationSelectItem[] {
  const result: LocationSelectItem[] = []
  const append = (items: LocationTreeNode[], depth: number) => {
    for (const item of sortLocationTree(items)) {
      result.push({ value: item.id, title: item.path, depth, location: item })
      append(item.children ?? [], depth + 1)
    }
  }
  append(nodes, 0)
  return result
}
