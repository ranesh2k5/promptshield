/**
 * API client – wraps fetch calls to the PromptShield backend.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

export interface ChatResponse {
  reply: string;
  flagged: boolean;
  flag_reason?: string;
  user_id?: string;
  role?: string;
}

export async function sendMessage(
  prompt: string,
  demoUser: string = "employee-1"
): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Demo-User": demoUser,
    },
    body: JSON.stringify({ prompt }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error ${res.status}: ${errorText}`);
  }

  return res.json() as Promise<ChatResponse>;
}
