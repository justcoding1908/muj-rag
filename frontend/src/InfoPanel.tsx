import { useEffect, useRef } from "react";
import { SOURCE_DOCUMENTS } from "./sources";

interface InfoPanelProps {
  view: "how" | "sources";
  onClose: () => void;
}

export default function InfoPanel({ view, onClose }: InfoPanelProps) {
  const closeRef = useRef<HTMLButtonElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    closeRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onCloseRef.current();
      } else if (event.key === "Tab") {
        event.preventDefault();
        closeRef.current?.focus();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      previousFocus?.focus();
    };
  }, []);

  return (
    <div className="panel-overlay" onClick={onClose}>
      <section
        className="panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="info-panel-heading"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="panel-header">
          <h2 id="info-panel-heading">{view === "how" ? "How this works" : "Source documents"}</h2>
          <button ref={closeRef} className="panel-close" type="button" onClick={onClose} aria-label="Close dialog">
            ×
          </button>
        </div>

        {view === "how" ? (
          <ul className="panel-list">
            <li>
              <strong>Grounded in 5 official documents.</strong> Every answer is drawn
              only from the text of MUJ's actual policy PDFs — never general knowledge.
            </li>
            <li>
              <strong>A hard refusal threshold runs before any AI call.</strong> If a
              question is nowhere close to the documents, it's refused immediately —
              that's a similarity-score check in code, not the AI's own judgment.
            </li>
            <li>
              <strong>Citations are verified, not trusted.</strong> After the AI
              answers, code checks every citation against what was actually retrieved.
              An answer that claims "found in document" but can't back that up with a
              real citation is overridden to a refusal — this was added after a test
              question got the AI to fabricate an answer.
            </li>
            <li>
              <strong>Tested against prompt injection.</strong> A set of adversarial
              questions (fake authority claims, embedded instructions, role-play
              jailbreaks) is run against this system to check it can't be talked into
              ignoring its own rules.
            </li>
            <li>
              <strong>Covered by automated tests</strong> that run on every code change,
              so a future edit can't silently break something that used to work.
            </li>
          </ul>
        ) : (
          <ul className="panel-list">
            {SOURCE_DOCUMENTS.map((doc) => (
              <li key={doc}>{doc}</li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
