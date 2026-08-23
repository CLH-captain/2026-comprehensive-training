export interface AgentContext {
  term_id?: number
  campus_id?: number
}

export interface AgentToolCall {
  name: string
  arguments: Record<string, unknown>
  success: boolean
  error?: string | null
}

export interface AgentChartSeries {
  name: string
  data: unknown[]
}

export interface AgentVisualization {
  type: 'bar' | 'line' | 'pie'
  title: string
  categories: string[]
  series: AgentChartSeries[]
}

export interface AgentChatResponse {
  conversation_id: number
  answer: string
  model_used: string
  tool_calls: AgentToolCall[]
  data: unknown
  visualization: AgentVisualization | null
}

export interface AgentConversation {
  id: number
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface AgentMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  model_used: string | null
  tool_calls: AgentToolCall[]
  created_at: string
}

export interface DictionaryItem {
  id: number
  name: string
}