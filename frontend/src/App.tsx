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

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    setError(null);
    const userMsg: Message = { role: "user", content: input };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput("");
    setLoading(true);

    try {
      const response = await sendMessage(history);
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
      setError(err?.message || "Failed to reach the server. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header>
        <h1>PromptShield</h1>
        <span className="badge">AI Agent Security Gateway</span>
      </header>

      <main className="chat-window">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Welcome to <strong>PromptShield</strong>.</p>
            <p className="subtitle">
              Send a message to test the security gateway. Try normal questions or prompt injections!
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

        {loading && <div className="message assistant loading">Analyzing & generating response…</div>}
        {error && <div className="error-banner">{error}</div>}
      </main>

      <footer className="input-bar">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Type a message or prompt injection test..."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading || !input.trim()}>
          {loading ? "..." : "Send"}
        </button>
      </footer>
    </div>
  );
}
