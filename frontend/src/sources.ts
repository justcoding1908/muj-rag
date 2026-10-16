// Mirrors DOC_NAMES in ingest.py — kept in sync by hand, same as api.ts's response types.
// `file` is the PDF's name under public/docs/ (a copy of the matching file in the repo's data/).
export const SOURCE_DOCUMENTS = [
  { name: "Academic Rules and Regulations 2024", file: "academic_rules_regulations_2024.pdf" },
  { name: "Attendance Monitoring Policy", file: "attendance_policy.pdf" },
  { name: "DoT Policy 2025-26", file: "dot_policy_2025_26.pdf" },
  { name: "Code of Ethics and Conduct", file: "code_of_ethics.pdf" },
  { name: "Plagiarism Policy 2016", file: "plagiarism_policy_2016.pdf" },
];

// URL of a source PDF, optionally jumping to a page (browsers' PDF viewers honour #page=N).
export function documentUrl(name: string, page?: number): string | null {
  const doc = SOURCE_DOCUMENTS.find((d) => d.name === name);
  if (!doc) return null;
  return `${import.meta.env.BASE_URL}docs/${doc.file}${page ? `#page=${page}` : ""}`;
}
