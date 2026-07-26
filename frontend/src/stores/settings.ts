import { defineStore } from 'pinia'

import { settingsApi } from '../services/settingsApi'
import type { ConfigurationRead, ConfigurationWrite } from '../types/settings'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    setupChecked: false,
    setupComplete: false,
    configuration: null as ConfigurationRead | null,
    loading: false,
    error: null as string | null
  }),
  actions: {
    async fetchSetupStatus(force = false) {
      if (this.setupChecked && !force) return this.setupComplete
      this.loading = true
      this.error = null
      try {
        const status = await settingsApi.setupStatus()
        this.setupComplete = status.completed
        this.setupChecked = true
        return status.completed
      } catch (reason) {
        this.error = reason instanceof Error ? reason.message : 'Setup-Status nicht verfügbar'
        throw reason
      } finally {
        this.loading = false
      }
    },
    async fetchConfiguration() {
      this.loading = true
      this.error = null
      try {
        this.configuration = await settingsApi.read()
        return this.configuration
      } catch (reason) {
        this.error = reason instanceof Error ? reason.message : 'Einstellungen nicht verfügbar'
        throw reason
      } finally {
        this.loading = false
      }
    },
    async completeSetup(payload: ConfigurationWrite) {
      this.loading = true
      this.error = null
      try {
        this.configuration = await settingsApi.complete(payload)
        this.setupComplete = true
        this.setupChecked = true
        return this.configuration
      } catch (reason) {
        this.error = reason instanceof Error ? reason.message : 'Einrichtung fehlgeschlagen'
        throw reason
      } finally {
        this.loading = false
      }
    },
    async saveConfiguration(payload: ConfigurationWrite) {
      this.loading = true
      this.error = null
      try {
        this.configuration = await settingsApi.update(payload)
        return this.configuration
      } catch (reason) {
        this.error = reason instanceof Error ? reason.message : 'Speichern fehlgeschlagen'
        throw reason
      } finally {
        this.loading = false
      }
    }
  }
})
