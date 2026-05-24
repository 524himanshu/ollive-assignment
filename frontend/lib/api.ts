import axios from "axios";

const BACKEND = typeof window !== "undefined"
  ? "http://localhost:8000"
  : (process.env.BACKEND_URL ?? "http://ollive-backend:8000");

const api = axios.create({
  baseURL: `${BACKEND}/api/v1`,
});

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  status: "active" | "cancelled";
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface DashboardStats {
  total_requests: number;
  success_rate: number;
  avg_latency_ms: number;
  total_tokens: number;
  error_count: number;
  pii_detected_count: number;
}

export const chatApi = {
  sendMessage: (message: string, conversation_id?: string) =>
    api.post("/chat/", { message, conversation_id }),

  getConversations: () =>
    api.get<Conversation[]>("/conversations/"),

  getConversation: (id: string) =>
    api.get<ConversationDetail>(`/conversations/${id}/`),

  cancelConversation: (id: string) =>
    api.patch(`/conversations/${id}/cancel/`),

  resumeConversation: (id: string) =>
    api.patch(`/conversations/${id}/resume/`),

  getDashboardStats: () =>
    api.get<DashboardStats>("/logs/dashboard/"),

  getRecentLogs: () =>
    api.get("/logs/recent/"),
};