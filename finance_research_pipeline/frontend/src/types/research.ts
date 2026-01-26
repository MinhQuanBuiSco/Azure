export type ResearchType =
  | 'comprehensive'
  | 'quick_analysis'
  | 'news_focused'
  | 'financial_only'

export type ResearchStatus =
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'cancelled'

export type AgentType =
  | 'supervisor'
  | 'web_research'
  | 'financial_data'
  | 'news_analysis'
  | 'analyst'
  | 'writer'
  | 'reviewer'

export type AgentStatus =
  | 'idle'
  | 'running'
  | 'completed'
  | 'error'
  | 'skipped'

export interface ResearchRequest {
  company_name: string
  ticker_symbol?: string
  research_type: ResearchType
  additional_context?: string
  include_competitors: boolean
  time_period_days: number
}

export interface ResearchResponse {
  research_id: string
  status: ResearchStatus
  company_name: string
  ticker_symbol?: string
  research_type: ResearchType
  created_at: string
  updated_at: string
  progress: number
  current_agent?: string
  error_message?: string
}

export interface AgentProgress {
  agent_type: AgentType
  status: AgentStatus
  message?: string
  progress: number
  started_at?: string
  completed_at?: string
  output_preview?: string
  error?: string
}

export interface PipelineProgress {
  research_id: string
  overall_progress: number
  current_agent?: AgentType
  agents: Record<string, AgentProgress>
  started_at: string
  estimated_completion?: string
}

export interface WebSocketMessage {
  type: 'agent_progress' | 'pipeline_progress' | 'complete' | 'error' | 'connected' | 'progress_update'
  research_id: string
  payload: Record<string, unknown>
  timestamp: string
}

export interface ResearchResult {
  research_id: string
  status: ResearchStatus
  company_name: string
  ticker_symbol?: string
  research_type: ResearchType
  created_at: string
  completed_at?: string
  executive_summary?: string
  market_analysis?: Record<string, unknown>
  financial_data?: Record<string, unknown>
  news_analysis?: Record<string, unknown>
  competitor_analysis?: Record<string, unknown>
  risk_assessment?: Record<string, unknown>
  recommendations?: string[]
  full_report?: string
}

export interface ReportListItem {
  research_id: string
  company_name: string
  ticker_symbol?: string
  research_type: ResearchType
  status: ResearchStatus
  created_at: string
  completed_at?: string
}

export interface ReportListResponse {
  reports: ReportListItem[]
  total: number
  page: number
  page_size: number
}

export const AGENT_CONFIG: Record<AgentType, { label: string; icon: string; color: string }> = {
  supervisor: { label: 'Supervisor', icon: '🎯', color: 'blue' },
  web_research: { label: 'Web Research', icon: '🌐', color: 'purple' },
  financial_data: { label: 'Financial Data', icon: '📊', color: 'green' },
  news_analysis: { label: 'News Analysis', icon: '📰', color: 'yellow' },
  analyst: { label: 'Analyst', icon: '🔬', color: 'pink' },
  writer: { label: 'Report Writer', icon: '✍️', color: 'cyan' },
  reviewer: { label: 'QA Reviewer', icon: '✅', color: 'emerald' },
}

export const RESEARCH_TYPE_OPTIONS = [
  { value: 'comprehensive', label: 'Comprehensive Analysis', description: 'Full research including all aspects' },
  { value: 'quick_analysis', label: 'Quick Analysis', description: 'Essential data and brief overview' },
  { value: 'news_focused', label: 'News Focused', description: 'Emphasize news and sentiment' },
  { value: 'financial_only', label: 'Financial Only', description: 'Focus on financial metrics' },
]
