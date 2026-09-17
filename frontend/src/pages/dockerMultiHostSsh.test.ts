import { describe, expect, it } from 'vitest'
import page from './WorkloadsPage.vue?raw'
import api from '../services/releaseApi.ts?raw'
import types from '../types/release.ts?raw'

describe('multi-host Docker monitoring', () => {
  it('manages multiple socket or SSH hosts independently', () => {
    expect(page).toContain('v-for="host in dockerHosts"')
    expect(page).toContain("connection_type === 'ssh'")
    expect(page).toContain('Server-Schlüssel abrufen')
    expect(page).toContain('Public Key für authorized_keys')
    expect(page).toContain('testDockerHost(host)')
    expect(page).toContain('syncDockerHost(host)')
    expect(page).toContain('v-for="item in filteredWorkloads"')
    expect(page).toContain('Nach Docker-Host filtern')
    expect(api).toContain('/workloads/docker/hosts/${id}/sync')
    expect(api).toContain('/workloads/docker/hosts/${id}/host-key/scan')
    expect(types).toContain("connection_type: 'socket' | 'ssh'")
  })
})
