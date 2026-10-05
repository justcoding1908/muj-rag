import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { askQuestion, ApiError, type Source } from "./api";
import InfoPanel from "./InfoPanel";
import "./App.css";

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "error";
  text: string;
  sources?: Source[];
  foundInDocument?: boolean;
}

const EXAMPLE_QUESTIONS = [
  {
    topic: "Academic rules",
    question: "What are the requirements to appear for end-semester exams?",
  },
  {
    topic: "Attendance",
    question: "What is the minimum attendance required for end-semester exams?",
  },
  {
    topic: "Discipline / DoT",
    question: "How many black DoTs can be awarded for a minor offence?",
  },
  {
    topic: "Code of ethics",
    question: "What responsibilities are covered by MUJ's Code of Ethics?",
  },
  {
    topic: "Plagiarism",
    question: "What is the penalty for plagiarism?",
  },
];

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [panel, setPanel] = useState<"how" | "sources" | null>(null);
  const [copyFeedback, setCopyFeedback] = useState<{
    messageId: string;
    status: "copied" | "failed";
  } | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const messageContentRefs = useRef(new Map<string, HTMLDivElement>());
  const copyFeedbackTimer = useRef<number | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    return () => {
      if (copyFeedbackTimer.current !== null) {
        window.clearTimeout(copyFeedbackTimer.current);
      }
    };
  }, []);

  function showCopyFeedback(messageId: string, status: "copied" | "failed") {
    if (copyFeedbackTimer.current !== null) {
      window.clearTimeout(copyFeedbackTimer.current);
    }
    setCopyFeedback({ messageId, status });
    copyFeedbackTimer.current = window.setTimeout(() => {
      setCopyFeedback((current) => current?.messageId === messageId ? null : current);
      copyFeedbackTimer.current = null;
    }, 2200);
  }

  async function copyAnswerWithSources(message: ChatMessage) {
    const answerText =
      messageContentRefs.current.get(message.id)?.innerText.trim() || message.text.trim();
    const citations = message.sources?.map((source) => `- ${source.document}, p.${source.page}`).join("\n");
    const clipboardText = citations
      ? `${answerText}\n\nSources:\n${citations}`
      : answerText;

    try {
      await navigator.clipboard.writeText(clipboardText);
      showCopyFeedback(message.id, "copied");
    } catch {
      showCopyFeedback(message.id, "failed");
    }
  }

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
        <div className="header-links">
          <button className="link-button" type="button" onClick={() => setPanel("how")}>
            How this works
          </button>
          <button className="link-button" type="button" onClick={() => setPanel("sources")}>
            Source documents
          </button>
        </div>
      </header>

      {panel && <InfoPanel view={panel} onClose={() => setPanel(null)} />}

      <main className="chat" aria-label="Conversation" aria-live="polite" aria-busy={loading}>
        {messages.length === 0 && (
          <div className="empty-state">
            <p>Try asking:</p>
            <div className="examples">
              {EXAMPLE_QUESTIONS.map(({ topic, question }) => (
                <button
                  key={topic}
                  className="example-chip"
                  type="button"
                  onClick={() => send(question)}
                  disabled={loading}
                >
                  <span className="example-topic">{topic}</span>
                  <span className="example-question">{question}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m) => (
          <article key={m.id} className={`message message-${m.role}`}>
            {m.role === "assistant" && !m.foundInDocument && (
              <span className="not-found-badge">Not in the documents</span>
            )}
            {m.role === "assistant" ? (
              <div
                className="message-text markdown"
                ref={(node) => {
                  if (node) {
                    messageContentRefs.current.set(m.id, node);
                  } else {
                    messageContentRefs.current.delete(m.id);
                  }
                }}
              >
                <ReactMarkdown>{m.text}</ReactMarkdown>
              </div>
            ) : (
              <p className="message-text">{m.text}</p>
            )}
            {m.sources && m.sources.length > 0 && (
              <div className="sources">
                {m.sources.map((s, i) => (
                  <span key={i} className="source-chip">
                    {s.document}, p.{s.page}
                  </span>
                ))}
              </div>
            )}
            {m.role === "assistant" && (
              <div className="message-actions">
                <button
                  className="copy-answer-button"
                  type="button"
                  onClick={() => void copyAnswerWithSources(m)}
                  aria-label={
                    copyFeedback?.messageId === m.id && copyFeedback.status === "failed"
                      ? "Copy failed. Try again."
                      : "Copy answer and citations"
                  }
                >
                  <span aria-live="polite">
                    {copyFeedback?.messageId === m.id
                      ? copyFeedback.status === "copied" ? "Copied!" : "Copy failed — try again"
                      : m.sources?.length ? "Copy answer + citations" : "Copy answer"}
                  </span>
                </button>
              </div>
            )}
          </article>
        ))}

        {loading && (
          <div className="message message-assistant message-loading" role="status" aria-label="Searching policy documents">
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
          aria-label="Ask a question about MUJ policy"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about MUJ policy..."
          maxLength={500}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !input.trim()} aria-label="Send question">
          Send
        </button>
      </form>
    </div>
  );
}
