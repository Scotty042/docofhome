export interface AboutLink {
  label: string
  url: string
  icon: string
}

export interface ReleaseNote {
  version: string
  title: string
  release_date: string | null
  markdown: string
  current: boolean
}

export interface AboutInformation {
  name: string
  slogan: string
  version: string
  project_summary: string
  data_sovereignty: string
  license_notice: string
  links: AboutLink[]
  releases: ReleaseNote[]
  feedback_available: boolean
  feedback_unavailable_reason: string | null
}

export type FeedbackCategory = 'error' | 'improvement' | 'usability' | 'documentation' | 'other'

export interface FeedbackTechnicalInfo {
  app_version: string | null
  route: string | null
  user_agent: string | null
  viewport: string | null
}

export interface FeedbackWrite {
  category: FeedbackCategory
  subject: string
  description: string
  current_page: string | null
  include_technical_info: boolean
  technical_info: FeedbackTechnicalInfo | null
}

export interface FeedbackResult {
  accepted: boolean
  message: string
  reference: string
}
