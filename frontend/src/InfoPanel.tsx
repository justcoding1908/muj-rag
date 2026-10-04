import { SOURCE_DOCUMENTS } from "./sources";

interface InfoPanelProps {
  view: "how" | "sources";
  onClose: () => void;
}

export default function InfoPanel({ view, onClose }: InfoPanelProps) {
  return (
    <div className="panel-overlay" onClick={onClose}>
      <div className="panel" onClick={(e) => e.stopPropagation()}>
        <div className="panel-header">
          <h2>{view === "how" ? "How this works" : "Source documents"}</h2>
          <button className="panel-close" onClick={onClose} aria-label="Close">
            ✕
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
      </div>
    </div>
  );
}
