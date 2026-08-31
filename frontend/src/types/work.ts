import type { KnowledgeTargetType } from './knowledge'

export type WorkItemType = 'task' | 'maintenance'
export type WorkStatus = 'open' | 'completed' | 'cancelled'
export type WorkPriority = 'low' | 'normal' | 'high'
export type RecurrenceMode = 'none' | 'interval' | 'calendar'
export type WorkSubjectType = 'device' | 'animal' | 'vehicle' | 'building' | 'room' | 'installation' | 'general' | 'other'
export type WorkActivityKind = 'general' | 'maintenance' | 'inspection' | 'repair' | 'measurement' | 'vaccination' | 'appointment' | 'official_inspection' | 'chimney_sweep' | 'service' | 'other'
export type WorkSubjectProfile = Record<string, string | number | boolean | null>

export interface WorkSubjectWrite {
  name: string
  subject_type: WorkSubjectType
  description: string | null
  profile: WorkSubjectProfile
}

export interface WorkSubjectRead extends WorkSubjectWrite {
  id: string
  created_at: string
  updated_at: string
  activity_count: number
}

export interface WorkItemWrite {
  item_type: WorkItemType
  activity_kind: WorkActivityKind
  title: string
  description: string | null
  target_type: KnowledgeTargetType | null
  target_id: string | null
  subject_id: string | null
  due_at: string | null
  recurrence_days: number | null
  recurrence_mode: RecurrenceMode
  calendar_months: number | null
  calendar_day: number | null
  calendar_month: number | null
  calendar_last_day: boolean
  priority: WorkPriority
}

export interface WorkItemRead extends WorkItemWrite {
  id: string
  subject_name: string | null
  subject_type: WorkSubjectType | null
  target_label: string | null
  target_route: string | null
  automation_key: string | null
  generated: boolean
  status: WorkStatus
  overdue: boolean
  due_status: 'upcoming' | 'today' | 'overdue' | null
  days_remaining: number | null
  completed_at: string | null
  history_count: number
  last_performed_at: string | null
  created_at: string
  updated_at: string
}

export interface WorkEventAttachment {
  id: string
  event_id: string
  file_name: string
  content_type: string
  size_bytes: number
  created_at: string
}

export interface WorkPaperlessLink {
  id: string
  event_id: string
  document_id: number
  title: string
  created_date: string | null
  original_file_name: string | null
  source_url: string | null
  created_at: string
}

export interface WorkItemEvent {
  id: string
  work_item_id: string
  event_type: string
  note: string | null
  due_at_before: string | null
  due_at_after: string | null
  occurred_at: string
  cost_amount: number | null
  cost_currency: string | null
  reading_value: number | null
  reading_unit: string | null
  interval_days: number | null
  attachments: WorkEventAttachment[]
  paperless_links: WorkPaperlessLink[]
  created_at: string
}

export interface WorkHistoryEntryWrite {
  note: string | null
  occurred_at: string
  cost_amount: number | null
  cost_currency: string | null
  reading_value: number | null
  reading_unit: string | null
}

export interface WorkCompletionWrite {
  note: string | null
  occurred_at: string | null
  cost_amount: number | null
  cost_currency: string | null
  reading_value: number | null
  reading_unit: string | null
}

export interface WorkHistoryStats {
  count: number
  last_performed_at: string | null
  previous_performed_at: string | null
  last_interval_days: number | null
  average_interval_days: number | null
  shortest_interval_days: number | null
  longest_interval_days: number | null
}

export interface WorkHistory {
  item_id: string
  stats: WorkHistoryStats
  entries: WorkItemEvent[]
}

export interface WorkSubjectTimelineEntry {
  id: string
  entry_type: 'history' | 'due'
  work_item_id: string
  title: string
  item_type: WorkItemType
  activity_kind: WorkActivityKind
  at: string
  note: string | null
  cost_amount: number | null
  cost_currency: string | null
  reading_value: number | null
  reading_unit: string | null
  status: WorkStatus | null
  paperless_links: WorkPaperlessLink[]
}

export interface WorkSubjectTimeline {
  subject: WorkSubjectRead
  entries: WorkSubjectTimelineEntry[]
}

export interface WorkSummary {
  open_total: number
  overdue: number
  due_next_7_days: number
  due_next_3_days: number
  due_today: number
  completed_total: number
}

export interface WorkListFilters {
  status?: WorkStatus
  itemType?: WorkItemType
  targetType?: KnowledgeTargetType
  targetId?: string
  subjectId?: string
}
