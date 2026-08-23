import { http } from '@/api/http'
import type {
  AgentChatResponse,
  AgentContext,
  AgentConversation,
  AgentMessage,
} from '@/types/agent'

export async function listAgentConversations(): Promise<AgentConversation[]> {
  return (await http.get<AgentConversation[]>('/agent/conversations')).data
}

export async function listAgentMessages(conversationId: number): Promise<AgentMessage[]> {
  return (await http.get<AgentMessage[]>(`/agent/conversations/${conversationId}/messages`)).data
}

export async function deleteAgentConversation(conversationId: number): Promise<void> {
  await http.delete(`/agent/conversations/${conversationId}`)
}

export async function sendAgentMessage(
  message: string,
  conversationId: number | null,
  context: AgentContext,
): Promise<AgentChatResponse> {
  return (
    await http.post<AgentChatResponse>(
      '/agent/chat',
      { message, conversation_id: conversationId, context },
      { timeout: 190_000 },
    )
  ).data
}