import { useChat } from '../context/ChatContext';

const ALL_FIELDS: { key: keyof ReturnType<typeof useChat>['caseSummary']; label: string }[] = [
  { key: 'symptom', label: 'Primary Symptom' },
  { key: 'duration', label: 'Duration' },
  { key: 'severity', label: 'Severity' },
  { key: 'temperature', label: 'Temperature' },
  { key: 'otherSymptoms', label: 'Other Symptoms' },
];

export function CaseSummaryPanel() {
  const { caseSummary, triageProgress } = useChat();

  if (!triageProgress.detectedSymptom) return null;

  const collected = ALL_FIELDS.filter((f) => {
    const val = caseSummary[f.key];
    return val !== null && val !== undefined && val !== '';
  });

  const pending = ALL_FIELDS.filter((f) => {
    const val = caseSummary[f.key];
    return val === null || val === undefined || val === '';
  });

  return (
    <aside className="case-summary-panel" aria-label="Case Summary">
      <div className="summary-header">
        <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 11l3 3L22 4" />
          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
        </svg>
        <span>Case Summary</span>
      </div>

      <div className="summary-body">
        {collected.map(({ key, label }) => (
          <div key={key} className="summary-field">
            <span className="field-label">{label}</span>
            <span className="field-value">{String(caseSummary[key])}</span>
          </div>
        ))}

        {caseSummary.additionalNotes.length > 0 && (
          <div className="summary-notes">
            <span className="field-label">Additional Notes</span>
            {caseSummary.additionalNotes.map((note, i) => (
              <span key={i} className="note-item">{note}</span>
            ))}
          </div>
        )}

        {pending.length > 0 && (
          <div className="summary-pending">
            <span className="pending-label">Pending Info</span>
            {pending.map(({ key, label }) => (
              <div key={key} className="pending-field">
                <span className="pending-dot" />
                <span className="pending-field-name">{label}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {triageProgress.isComplete && (
        <div className="summary-complete-badge">
          <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          Assessment Complete
        </div>
      )}
    </aside>
  );
}
