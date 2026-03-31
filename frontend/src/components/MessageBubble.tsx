import { useChat } from '../context/ChatContext';
import type { Message, Classification, SeverityLevel } from '../types';

// ─── Classification Label ─────────────────────────────────────────────────────
function ClassificationLabel({ classification }: { classification: Classification }) {
  if (classification === 'triage') {
    return (
      <div className="classification-label label-triage">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
          <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
        </svg>
        Triage Step
      </div>
    );
  }
  if (classification === 'insight') {
    return (
      <div className="classification-label label-insight">
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="12" y1="2" x2="12" y2="6" />
          <line x1="12" y1="18" x2="12" y2="22" />
          <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
          <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
          <line x1="2" y1="12" x2="6" y2="12" />
          <line x1="18" y1="12" x2="22" y2="12" />
          <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
          <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
        </svg>
        Clinical Insight
      </div>
    );
  }
  return (
    <div className="classification-label label-general">
      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
        fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
      System Response
    </div>
  );
}

// ─── Severity Indicator ───────────────────────────────────────────────────────
function SeverityIndicator({ severity }: { severity: SeverityLevel }) {
  if (!severity) return null;

  const config: Record<NonNullable<SeverityLevel>, { label: string; className: string }> = {
    low:      { label: '● Low Severity',      className: 'severity-low' },
    moderate: { label: '● Moderate Severity', className: 'severity-moderate' },
    high:     { label: '▲ High Severity',      className: 'severity-high' },
    critical: { label: '⚠ Critical – Seek Emergency Care', className: 'severity-critical' },
  };

  const { label, className } = config[severity];
  return <div className={`severity-indicator ${className}`}>{label}</div>;
}

// ─── Triage Question Card ─────────────────────────────────────────────────────
function TriageQuestionCard({ lines }: { lines: string[] }) {
  return (
    <div className="triage-question-card">
      <div className="triage-card-header">
        <span>🩺</span>
        <span>Additional Information Required</span>
      </div>
      <ol className="triage-question-list">
        {lines.map((line, i) => (
          <li key={i} className="triage-question-item">
            <span className="question-badge">{i + 1}</span>
            <span>{line}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

// ─── Format Content ───────────────────────────────────────────────────────────
function formatContent(content: string, classification?: Classification) {
  const parts = content.split('⚠️');
  const mainContent = parts[0].trim();
  const disclaimer = parts[1] ? parts[1].trim() : null;

  const lines = mainContent.split('\n').filter((l) => l.trim() !== '');

  const elements: React.ReactNode[] = [];
  let questionBuffer: string[] = [];
  let numberedBuffer: string[] = [];

  const flushNumbered = () => {
    if (numberedBuffer.length > 0) {
      elements.push(
        <ol key={`ol-${elements.length}`} className="formatted-list">
          {numberedBuffer.map((item, i) => (
            <li key={i} className="formatted-list-item">
              <span className="list-num">{i + 1}</span>
              <span dangerouslySetInnerHTML={{ __html: parseBold(item) }} />
            </li>
          ))}
        </ol>
      );
      numberedBuffer = [];
    }
  };

  const flushQuestions = () => {
    if (questionBuffer.length > 0) {
      elements.push(<TriageQuestionCard key={`tq-${elements.length}`} lines={questionBuffer} />);
      questionBuffer = [];
    }
  };

  for (const line of lines) {
    const numberedMatch = line.match(/^\d+\.\s+(.+)/);
    const isQuestion = classification === 'triage' && line.trim().endsWith('?');

    if (isQuestion) {
      flushNumbered();
      questionBuffer.push(line.replace(/^\d+\.\s*/, '').trim());
    } else if (numberedMatch) {
      flushQuestions();
      numberedBuffer.push(numberedMatch[1]);
    } else {
      flushQuestions();
      flushNumbered();
      if (line.trim()) {
        elements.push(
          <p key={`p-${elements.length}`} className="content-paragraph"
            dangerouslySetInnerHTML={{ __html: parseBold(line) }} />
        );
      }
    }
  }

  flushQuestions();
  flushNumbered();

  return (
    <>
      {elements}
      {disclaimer && (
        <div className="disclaimer-box">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <span dangerouslySetInnerHTML={{ __html: parseBold(disclaimer) }} />
        </div>
      )}
    </>
  );
}

function parseBold(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}

// ─── Message Bubble ───────────────────────────────────────────────────────────
interface Props {
  message: Message;
}

function getQuickOptions(content: string): string[] {
  const lower = content.toLowerCase();
  if (lower.includes('severity') || lower.includes('scale')) {
    return ['Mild (1-3)', 'Moderate (4-6)', 'Severe (7-10)'];
  }
  if (lower.includes('duration') || lower.includes('long have you')) {
    return ['< 1 day', '1-3 days', '> 3 days'];
  }
  if (lower.includes('associated') || lower.includes('other symptoms')) {
    return ['Yes, I have other symptoms', 'No other symptoms'];
  }
  return [];
}

export function MessageBubble({ message }: Props) {
  const { setInputValue } = useChat();
  const isUser = message.role === 'user';
  const isAsk = message.status === 'ASK';

  const time = new Date(message.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  if (isUser) {
    return (
      <div className="message-row user-row">
        <div className="user-bubble-group" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
          <div className="bubble user-bubble">
            <p>{message.content}</p>
          </div>
          <span className="message-time" style={{ opacity: 0.6, fontSize: '0.7rem', marginTop: '4px' }}>{time}</span>
        </div>
        <div className="avatar user-avatar">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className="message-row assistant-row">
      <div className="avatar assistant-avatar">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
      </div>
      <div className="assistant-bubble-group" style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
          {message.classification && (
            <ClassificationLabel classification={message.classification} />
          )}
          <span className="message-time" style={{ opacity: 0.6 }}>{time}</span>
        </div>
        
        {message.severity && <SeverityIndicator severity={message.severity ?? null} />}
        
        <div className={isAsk ? 'triage-ask-card-wrapper' : 'bubble assistant-bubble'}>
          {formatContent(message.content, message.classification)}
          
          {isAsk && (() => {
            const opts = getQuickOptions(message.content);
            if (opts.length > 0) {
              return (
                <div className="quick-select-options">
                  {opts.map(opt => (
                    <button key={opt} className="quick-select-action" onClick={() => setInputValue(opt)}>
                      {opt}
                    </button>
                  ))}
                </div>
              );
            }
            return null;
          })()}
        </div>
      </div>
    </div>
  );
}
