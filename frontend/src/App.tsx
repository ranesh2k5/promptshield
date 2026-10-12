import { useState } from "react";
import { sendMessage } from "./api";

interface Message {
  role: "user" | "assistant";
  content: string;
  flagged?: boolean;
}

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentUser, setCurrentUser] = useState<"employee-1" | "admin-1">("employee-1");

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    setError(null);
    const userPrompt = input;
    const history = [...messages, { role: "user" as const, content: userPrompt }];
    setMessages(history);
    setInput("");
    setLoading(true);

    try {
      const response = await sendMessage(userPrompt, currentUser);
      setMessages([
        ...history,
        {
          role: "assistant",
          content: response.reply,
          flagged: response.flagged,
        },
      ]);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to communicate with PromptShield gateway.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <div>
          <h1>PromptShield</h1>
          <span className="badge">AI Agent Security Gateway</span>
        </div>

        <div className="user-toggle">
          <label htmlFor="user-select">Active Persona: </label>
          <select
            id="user-select"
            value={currentUser}
            onChange={(e) => setCurrentUser(e.target.value as any)}
          >
            <option value="employee-1">employee-1 (Role: Employee)</option>
            <option value="admin-1">admin-1 (Role: Admin)</option>
          </select>
        </div>
      </header>

      <main className="chat-window">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Welcome to <strong>PromptShield</strong>.</p>
            <p className="subtitle">
              Send messages as <strong>{currentUser}</strong>. The gateway enforces prompt injection filters and server-side authorization.
            </p>
          </div>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`message ${m.role} ${m.flagged ? "flagged" : ""}`}
          >
            <strong>{m.role === "user" ? "You" : "Shield"}:</strong> {m.content}
          </div>
        ))}

        {loading && <div className="message assistant loading">Evaluating prompt & policy…</div>}
        {error && <div className="error-banner">{error}</div>}
      </main>

      <footer className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type a message or injection test..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          {loading ? "..." : "Send"}
        </button>
      </footer>
    </div>
  );
}
