import { useEffect, useRef, useState } from "react";
import { askQuestion, ApiError, type Source } from "./api";
import "./App.css";

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "error";
  text: string;
  sources?: Source[];
  foundInDocument?: boolean;
}

const EXAMPLE_QUESTIONS = [
  "What is the minimum attendance percentage required to write the end-semester exam?",
  "How many black DoTs can be awarded for a minor offence?",
  "What is the penalty for plagiarism?",
];

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(question: string) {
    const text = question.trim();
    if (!text || loading) return;

    setMessages((prev) => [...prev, { id: newId(), role: "user", text }]);
    setInput("");
    setLoading(true);

    try {
      const result = await askQuestion(text);
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: "assistant",
          text: result.answer,
          sources: result.sources,
          foundInDocument: result.found_in_document,
        },
      ]);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Couldn't reach the assistant. Please try again.";
      setMessages((prev) => [...prev, { id: newId(), role: "error", text: message }]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="page">
      <header className="header">
        <h1>MUJ Policy Assistant</h1>
        <p>Ask about academic rules, attendance, discipline, ethics, or plagiarism policy.</p>
      </header>

      <main className="chat">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Try asking:</p>
            <div className="examples">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button key={q} className="example-chip" onClick={() => send(q)} disabled={loading}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <div key={m.id} className={`message message-${m.role}`}>
            {m.role === "assistant" && !m.foundInDocument && (
              <span className="not-found-badge">Not in the documents</span>
            )}
            <p className="message-text">{m.text}</p>
            {m.sources && m.sources.length > 0 && (
              <div className="sources">
                {m.sources.map((s, i) => (
                  <span key={i} className="source-chip">
                    {s.document}, p.{s.page}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message message-assistant message-loading">
            <span className="dot" />
            <span className="dot" />
            <span className="dot" />
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <form className="composer" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about MUJ policy..."
          maxLength={500}
          disabled={loading}
          autoFocus
        />
        <button type="submit" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
    </div>
  );
}
