export type QualitySeverity = 'error' | 'warning' | 'info'

export interface QualityIssue {
  id: string
  category: string
  severity: QualitySeverity
  code: string
  title: string
  description: string
  target_type: string | null
  target_id: string | null
  route: string | null
  created_at: string
}

export interface QualityReport {
  id: string
  trigger: string
  score: number
  issue_count: number
  error_count: number
  warning_count: number
  info_count: number
  started_at: string
  completed_at: string
  issues: QualityIssue[]
}
