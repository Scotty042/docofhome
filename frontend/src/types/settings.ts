export type IntegrationKind = 'home_assistant' | 'immich' | 'nextcloud' | 'fritzbox' | 'paperless'
export type Language = 'de' | 'en'
export type ThemePreference = 'dark' | 'light'
export type ModuleKey = 'locations' | 'electrical' | 'assets' | 'master_data' | 'network' | 'smart_home' | 'consumption' | 'wiki' | 'maintenance' | 'quality' | 'cookbook' | 'images' | 'documents' | 'workloads'

export type McpPermission = 'read' | 'write' | 'admin'

export interface McpSettingsRead {
  enabled: boolean
  permission: McpPermission
  public_url: string | null
  token_configured: boolean
}

export interface McpSettingsWrite {
  enabled: boolean
  permission: McpPermission
  public_url: string | null
}

export interface McpTokenCreated {
  token: string
  settings: McpSettingsRead
}

export interface SetupStatus {
  setup_required: boolean
  completed: boolean
}

export interface HealthRead {
  status: string
  name: string
  version: string
}

export interface IntegrationRead {
  kind: IntegrationKind
  enabled: boolean
  base_url: string | null
  browser_url?: string | null
  account: string | null
  secret_configured: boolean
  selected_album_id: string | null
  document_root: string | null
}

export interface IntegrationWrite {
  kind: IntegrationKind
  enabled: boolean
  base_url: string | null
  browser_url?: string | null
  account: string | null
  secret?: string
  selected_album_id: string | null
  document_root: string | null
}

export interface IntegrationTestResult {
  kind: IntegrationKind
  success: boolean
  message: string
  service_version: string | null
  response_time_ms: number
}


export interface ConfigurationRead {
  installation_name: string
  language: Language
  timezone: string
  theme: ThemePreference
  online_product_image_search_enabled: boolean
  product_image_source_wikimedia_enabled: boolean
  product_image_source_duckduckgo_enabled: boolean
  enabled_modules?: ModuleKey[]
  main_menu_modules?: ModuleKey[]
  setup_completed_at: string
  integrations: IntegrationRead[]
}

export interface ConfigurationWrite {
  installation_name: string
  language: Language
  timezone: string
  theme: ThemePreference
  online_product_image_search_enabled: boolean
  product_image_source_wikimedia_enabled: boolean
  product_image_source_duckduckgo_enabled: boolean
  enabled_modules?: ModuleKey[]
  main_menu_modules?: ModuleKey[]
  integrations: IntegrationWrite[]
}

export const integrationKinds: IntegrationKind[] = [
  'home_assistant',
  'immich',
  'nextcloud',
  'fritzbox',
  'paperless'
]

export const moduleKeys: ModuleKey[] = [
  'locations',
  'electrical',
  'assets',
  'master_data',
  'network',
  'smart_home',
  'consumption',
  'wiki',
  'maintenance',
  'quality',
  'cookbook',
  'images',
  'documents',
  'workloads'
]


export function createDefaultConfiguration(): ConfigurationWrite {
  return {
    installation_name: '',
    language: 'de',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    theme: 'dark',
    online_product_image_search_enabled: false,
    product_image_source_wikimedia_enabled: true,
    product_image_source_duckduckgo_enabled: true,
    enabled_modules: [...moduleKeys],
    main_menu_modules: [...moduleKeys],
    integrations: integrationKinds.map((kind) => ({
      kind,
      enabled: false,
      base_url: null,
      browser_url: null,
      account: null,
      selected_album_id: null,
      document_root: kind === 'nextcloud' ? 'docofhome/Documents' : null,
      secret: ''
    }))
  }
}

export function editableConfiguration(configuration: ConfigurationRead): ConfigurationWrite {
  return {
    installation_name: configuration.installation_name,
    language: configuration.language,
    timezone: configuration.timezone,
    theme: configuration.theme,
    online_product_image_search_enabled: configuration.online_product_image_search_enabled,
    product_image_source_wikimedia_enabled: configuration.product_image_source_wikimedia_enabled,
    product_image_source_duckduckgo_enabled: configuration.product_image_source_duckduckgo_enabled,
    enabled_modules: [...(configuration.enabled_modules ?? moduleKeys)],
    main_menu_modules: [...(configuration.main_menu_modules ?? configuration.enabled_modules ?? moduleKeys)],
    integrations: integrationKinds.map((kind) => {
      const stored = configuration.integrations.find((integration) => integration.kind === kind)
      return {
        kind,
        enabled: stored?.enabled ?? false,
        base_url: stored?.base_url ?? null,
        browser_url: stored?.browser_url ?? null,
        account: stored?.account ?? null,
        selected_album_id: stored?.selected_album_id ?? null,
        document_root: kind === 'nextcloud'
          ? stored?.document_root ?? 'docofhome/Documents'
          : null,
        secret: ''
      }
    })
  }
}
