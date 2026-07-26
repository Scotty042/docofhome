import type {
  Distribution,
  DistributionTreeNode,
  ElectricalCabinetComponent,
  ElectricalPhase,
  FlatDistribution,
  ProtectiveDevice,
  ProtectiveDeviceType
} from '../types/electrical'

export const protectiveDeviceLabels: Record<ProtectiveDeviceType, string> = {
  fuse: 'Sicherung',
  rcd: 'FI / RCD',
  mcb: 'LS / MCB',
  rcbo: 'FI/LS / RCBO',
  spd: 'Überspannungsschutz'
}

export function flattenDistributionTree(
  roots: DistributionTreeNode[]
): FlatDistribution[] {
  const result: FlatDistribution[] = []
  const visit = (node: DistributionTreeNode, depth: number) => {
    result.push({ distribution: node, depth })
    node.children.forEach((child) => visit(child, depth + 1))
  }
  roots.forEach((root) => visit(root, 0))
  return result
}

export function eligibleParentDistributions(
  roots: DistributionTreeNode[],
  currentId: string | null
): FlatDistribution[] {
  if (!currentId) return flattenDistributionTree(roots)
  const excluded = new Set<string>([currentId])
  const collectDescendants = (node: DistributionTreeNode, belowCurrent: boolean) => {
    const isBelow = belowCurrent || node.id === currentId
    if (isBelow) excluded.add(node.id)
    node.children.forEach((child) => collectDescendants(child, isBelow))
  }
  roots.forEach((root) => collectDescendants(root, false))
  return flattenDistributionTree(roots).filter(
    ({ distribution }) => !excluded.has(distribution.id) && !distribution.deleted_at
  )
}

export function filterDistributionTree(
  roots: DistributionTreeNode[],
  search: string,
  distributionType: '' | 'main' | 'sub'
): DistributionTreeNode[] {
  const normalizedSearch = search.trim().toLocaleLowerCase()
  const visit = (node: DistributionTreeNode): DistributionTreeNode | null => {
    const children = node.children
      .map(visit)
      .filter((child): child is DistributionTreeNode => child !== null)
    const matchesType = !distributionType || node.distribution_type === distributionType
    const matchesSearch = !normalizedSearch || [
      node.display_name,
      node.asset.name,
      node.asset.jarvis_code,
      node.asset.location_path
    ].some((value) => value.toLocaleLowerCase().includes(normalizedSearch))
    if ((!matchesType || !matchesSearch) && children.length === 0) return null
    return { ...node, children }
  }
  return roots.map(visit).filter((node): node is DistributionTreeNode => node !== null)
}

export interface DeviceRowGroup {
  row: number | null
  devices: ProtectiveDevice[]
}

export interface DeviceModulePlacement {
  device: ProtectiveDevice
  gridColumn: string
  start: number
  end: number
}

export function groupProtectiveDevices(
  devices: ProtectiveDevice[],
  configuredRows: number | null = null
): DeviceRowGroup[] {
  const rows = new Map<number | null, ProtectiveDevice[]>()
  devices.forEach((device) => {
    const row = device.row_number
    const entries = rows.get(row) ?? []
    entries.push(device)
    rows.set(row, entries)
  })
  if (configuredRows !== null) {
    for (let row = 1; row <= configuredRows; row += 1) {
      if (!rows.has(row)) rows.set(row, [])
    }
  }
  return [...rows.entries()]
    .map(([row, entries]) => ({
      row,
      devices: [...entries].sort((left, right) => (
        (left.start_position ?? Number.MAX_SAFE_INTEGER)
        - (right.start_position ?? Number.MAX_SAFE_INTEGER)
        || left.asset.name.localeCompare(right.asset.name)
      ))
    }))
    .sort((left, right) => (
      (left.row ?? Number.MAX_SAFE_INTEGER) - (right.row ?? Number.MAX_SAFE_INTEGER)
    ))
}

export function modulePlacements(devices: ProtectiveDevice[]): DeviceModulePlacement[] {
  return devices.flatMap((device) => {
    if (device.start_position === null || device.module_width === null) return []
    const start = device.start_position
    const end = start + device.module_width - 1
    return [{
      device,
      start,
      end,
      gridColumn: `${start} / span ${device.module_width}`
    }]
  })
}


export function busbarPhasePattern(
  component: Pick<ElectricalCabinetComponent, 'phases' | 'start_phase' | 'module_width'>
): ElectricalPhase[] {
  const enabled = component.phases.filter((phase): phase is ElectricalPhase => (
    phase === 'L1' || phase === 'L2' || phase === 'L3'
  ))
  if (!enabled.length || component.module_width < 1) return []
  const standard: ElectricalPhase[] = ['L1', 'L2', 'L3']
  const start = component.start_phase && enabled.includes(component.start_phase)
    ? component.start_phase
    : enabled[0]
  const index = standard.indexOf(start)
  const rotated = [...standard.slice(index), ...standard.slice(0, index)]
    .filter((phase) => enabled.includes(phase))
  return Array.from(
    { length: component.module_width },
    (_, offset) => rotated[offset % rotated.length]
  )
}

export function moduleNumbers(modulesPerRow: number): number[] {
  return Array.from({ length: modulesPerRow }, (_, index) => index + 1)
}

export function moduleBoardStyle(modulesPerRow: number): {
  gridTemplateColumns: string
  minWidth: string
} {
  const modules = Math.max(1, Math.trunc(modulesPerRow))
  const moduleWidth = 34
  const gap = 4
  return {
    gridTemplateColumns: `repeat(${modules}, minmax(${moduleWidth}px, 1fr))`,
    minWidth: `${modules * moduleWidth + (modules - 1) * gap}px`
  }
}

export function moduleDropConflict(
  devices: ProtectiveDevice[],
  movingDeviceId: string,
  start: number,
  width: number,
  modulesPerRow: number
): string | null {
  if (start < 1 || width < 1) return 'Startposition und Breite müssen mindestens 1 sein.'
  const end = start + width - 1
  if (end > modulesPerRow) {
    return `Das Gerät würde bis Modul ${end} reichen; die Reihe endet bei Modul ${modulesPerRow}.`
  }
  const overlap = devices.find((device) => {
    if (
      device.id === movingDeviceId
      || device.start_position === null
      || device.module_width === null
    ) return false
    const deviceEnd = device.start_position + device.module_width - 1
    return start <= deviceEnd && end >= device.start_position
  })
  return overlap ? `Die Position überschneidet sich mit „${overlap.asset.name}“.` : null
}

export function distributionCapacity(distribution: Distribution): string {
  if (distribution.rows === null && distribution.modules_per_row === null) return 'Unbekannt'
  const rows = distribution.rows === null ? '? Reihen' : `${distribution.rows} Reihen`
  const modules = distribution.modules_per_row === null
    ? '? Module je Reihe'
    : `${distribution.modules_per_row} Module je Reihe`
  return `${rows} · ${modules}`
}
