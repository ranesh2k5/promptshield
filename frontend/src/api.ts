/**
 * API client – wraps fetch calls to the PromptShield backend.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResponse {
  reply: string;
  flagged: boolean;
  flag_reason?: string;
}

export async function sendMessage(messages: Message[]): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }

  return res.json() as Promise<ChatResponse>;
}
