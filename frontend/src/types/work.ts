import type { KnowledgeTargetType } from './knowledge'

export type WorkItemType = 'task' | 'maintenance'
export type WorkStatus = 'open' | 'completed' | 'cancelled'
export type WorkPriority = 'low' | 'normal' | 'high'
export type RecurrenceMode = 'none' | 'interval' | 'calendar'

export interface WorkItemWrite {
  item_type: WorkItemType
  title: string
  description: string | null
  target_type: KnowledgeTargetType | null
  target_id: string | null
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
  target_label: string | null
  target_route: string | null
  automation_key: string | null
  generated: boolean
  status: WorkStatus
  overdue: boolean
  due_status: 'upcoming' | 'today' | 'overdue' | null
  days_remaining: number | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface WorkItemEvent {
  id: string
  work_item_id: string
  event_type: string
  note: string | null
  due_at_before: string | null
  due_at_after: string | null
  created_at: string
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
}
