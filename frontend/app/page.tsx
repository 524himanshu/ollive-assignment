"use client";

import { useState, useEffect, useRef } from "react";
import { chatApi, Conversation, Message, DashboardStats } from "@/lib/api";

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [view, setView] = useState<"chat" | "dashboard">("chat");
  const [recentLogs, setRecentLogs] = useState<any[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadConversations();
    loadStats();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const loadConversations = async () => {
    try {
      const res = await chatApi.getConversations();
      setConversations(res.data);
    } catch (e) {}
  };

  const loadStats = async () => {
    try {
      const [statsRes, logsRes] = await Promise.all([
        chatApi.getDashboardStats(),
        chatApi.getRecentLogs(),
      ]);
      setStats(statsRes.data);
      setRecentLogs(logsRes.data);
    } catch (e) {}
  };

  const loadConversation = async (id: string) => {
    try {
      const res = await chatApi.getConversation(id);
      setActiveConversationId(id);
      setMessages(res.data.messages);
    } catch (e) {}
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setLoading(true);

    const tempUser: Message = {
      id: "temp-user",
      conversation_id: activeConversationId || "",
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUser]);

    try {
      const res = await chatApi.sendMessage(text, activeConversationId || undefined);
      const { conversation_id, message, response } = res.data;
      setActiveConversationId(conversation_id);
      setMessages((prev) => [
        ...prev.filter((m) => m.id !== "temp-user"),
        message,
        response,
      ]);
      loadConversations();
      loadStats();
    } catch (e) {
      setMessages((prev) => prev.filter((m) => m.id !== "temp-user"));
    } finally {
      setLoading(false);
    }
  };

  const cancelConversation = async () => {
    if (!activeConversationId) return;
    await chatApi.cancelConversation(activeConversationId);
    loadConversations();
  };

  const resumeConversation = async (id: string) => {
    await chatApi.resumeConversation(id);
    loadConversations();
    loadConversation(id);
  };

  const newConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
  };

  const activeConversation = conversations.find((c) => c.id === activeConversationId);
  const isCancelled = activeConversation?.status === "cancelled";

  return (
    <div className="flex h-screen bg-[#0f0f0f] text-white overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 flex flex-col border-r border-white/10 bg-[#141414]">
        <div className="p-4 border-b border-white/10">
          <h1 className="text-lg font-bold text-white">Ollive</h1>
          <p className="text-xs text-white/40">Inference Logger</p>
        </div>

        {/* Nav */}
        <div className="flex border-b border-white/10">
          <button
            onClick={() => setView("chat")}
            className={`flex-1 py-2 text-sm ${view === "chat" ? "text-white border-b-2 border-white" : "text-white/40"}`}
          >
            Chat
          </button>
          <button
            onClick={() => { setView("dashboard"); loadStats(); }}
            className={`flex-1 py-2 text-sm ${view === "dashboard" ? "text-white border-b-2 border-white" : "text-white/40"}`}
          >
            Dashboard
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto p-2">
          <button
            onClick={newConversation}
            className="w-full mb-2 p-2 rounded bg-white/5 hover:bg-white/10 text-sm text-left text-white/70"
          >
            + New conversation
          </button>
          {conversations.map((c) => (
            <div
              key={c.id}
              onClick={() => loadConversation(c.id)}
              className={`p-2 rounded cursor-pointer mb-1 text-sm group flex items-center justify-between ${
                c.id === activeConversationId ? "bg-white/10" : "hover:bg-white/5"
              }`}
            >
              <span className={`truncate flex-1 ${c.status === "cancelled" ? "text-white/30 line-through" : "text-white/70"}`}>
                {c.title || "Untitled"}
              </span>
              {c.status === "cancelled" && (
                <button
                  onClick={(e) => { e.stopPropagation(); resumeConversation(c.id); }}
                  className="text-xs text-blue-400 ml-1 opacity-0 group-hover:opacity-100"
                >
                  Resume
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main Area */}
      <div className="flex-1 flex flex-col">
        {view === "chat" ? (
          <>
            {/* Chat Header */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-white/10">
              <span className="text-sm text-white/50">
                {activeConversation?.title || "New conversation"}
                {isCancelled && <span className="ml-2 text-red-400 text-xs">(cancelled)</span>}
              </span>
              {activeConversationId && !isCancelled && (
                <button
                  onClick={cancelConversation}
                  className="text-xs text-red-400 hover:text-red-300 border border-red-400/30 px-3 py-1 rounded"
                >
                  Cancel conversation
                </button>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-white/20">
                  <p className="text-2xl mb-2">💬</p>
                  <p className="text-sm">Start a conversation</p>
                </div>
              )}
              {messages.map((msg) => (
                <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[70%] px-4 py-2 rounded-2xl text-sm ${
                    msg.role === "user"
                      ? "bg-white text-black rounded-br-sm"
                      : "bg-white/10 text-white/90 rounded-bl-sm"
                  }`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-white/10 px-4 py-2 rounded-2xl rounded-bl-sm text-sm text-white/40">
                    Thinking...
                  </div>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input */}
            <div className="px-6 py-4 border-t border-white/10">
              {isCancelled ? (
                <div className="text-center text-sm text-white/30 py-2">
                  This conversation is cancelled.{" "}
                  <button
                    onClick={() => resumeConversation(activeConversationId!)}
                    className="text-blue-400 hover:underline"
                  >
                    Resume it
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                    placeholder="Type a message..."
                    className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm outline-none focus:border-white/30 placeholder:text-white/20"
                  />
                  <button
                    onClick={sendMessage}
                    disabled={loading || !input.trim()}
                    className="px-4 py-2 bg-white text-black text-sm rounded-xl disabled:opacity-30 hover:bg-white/90"
                  >
                    Send
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Dashboard */
          <div className="flex-1 overflow-y-auto p-6">
            <h2 className="text-lg font-semibold mb-6">Inference Dashboard</h2>

            {/* Stats Grid */}
            {stats && (
              <div className="grid grid-cols-3 gap-4 mb-8">
                {[
                  { label: "Total Requests", value: stats.total_requests },
                  { label: "Success Rate", value: `${stats.success_rate}%` },
                  { label: "Avg Latency", value: `${stats.avg_latency_ms}ms` },
                  { label: "Total Tokens", value: stats.total_tokens },
                  { label: "Errors", value: stats.error_count },
                  { label: "PII Detected", value: stats.pii_detected_count },
                ].map((s) => (
                  <div key={s.label} className="bg-white/5 rounded-xl p-4 border border-white/10">
                    <p className="text-xs text-white/40 mb-1">{s.label}</p>
                    <p className="text-2xl font-bold">{s.value}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Recent Logs Table */}
            <h3 className="text-sm font-semibold text-white/60 mb-3">Recent Inference Logs</h3>
            <div className="overflow-x-auto rounded-xl border border-white/10">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10 text-white/40">
                    <th className="text-left px-4 py-3">Model</th>
                    <th className="text-left px-4 py-3">Status</th>
                    <th className="text-left px-4 py-3">Latency</th>
                    <th className="text-left px-4 py-3">Tokens</th>
                    <th className="text-left px-4 py-3">PII</th>
                    <th className="text-left px-4 py-3">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {recentLogs.map((log) => (
                    <tr key={log.id} className="border-b border-white/5 hover:bg-white/5">
                      <td className="px-4 py-3 text-white/70">{log.model}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs ${
                          log.status === "success" ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
                        }`}>
                          {log.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-white/70">{log.latency_ms}ms</td>
                      <td className="px-4 py-3 text-white/70">{log.total_tokens ?? "—"}</td>
                      <td className="px-4 py-3">
                        {log.pii_detected ? (
                          <span className="text-yellow-400">⚠ Yes</span>
                        ) : (
                          <span className="text-white/30">No</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-white/40">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}