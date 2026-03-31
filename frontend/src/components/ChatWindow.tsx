import { useEffect, useRef } from 'react';
import { useChat } from '../context/ChatContext';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';
import { TriageProgressBar } from './TriageProgressBar';
import { CaseSummaryPanel } from './CaseSummaryPanel';
import { InputBox } from './InputBox';
import { ThemeToggle } from './ThemeToggle';

const QUICK_START = [
  { label: '🌡 Fever', symptom: 'I have a fever' },
  { label: '🤕 Headache', symptom: 'I have a headache' },
  { label: '💔 Chest Pain', symptom: 'I have chest pain' },
  { label: '😮‍💨 Breathing Issues', symptom: 'I am having difficulty breathing' },
  { label: '🤢 Abdominal Pain', symptom: 'I have abdominal pain' },
];

export function ChatWindow() {
  const { messages, isLoading, loadingPhase, triageProgress, sendMessage, setIsCustomInput } = useChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  const currentSymptom = [...messages].reverse().find(m => m.role === 'assistant')?.meta?.symptom || 'unknown';

  // Auto-scroll
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleQuickStart = (symptom: string) => {
    setIsCustomInput(false);
    sendMessage(symptom);
  };

  const handleOtherSymptom = () => {
    setIsCustomInput(true);
    setTimeout(() => {
      document.getElementById('chat-input')?.focus();
    }, 50);
  };

  const showSummaryPanel = !!triageProgress.detectedSymptom;

  return (
    <div className="chat-window">
      {/* Header */}
      <header className="chat-header">
        <div className="chat-header-left">
          <div className="header-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <div>
            <h1 className="chat-title">MedAssist AI</h1>
            <div className="chat-subtitle" style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              Intelligent Symptom Triage
              {currentSymptom !== 'unknown' && (
                <span className="symptom-badge" style={{ fontSize: '10px', padding: '2px 6px', fontWeight: 600 }}>
                  Active Symptom: {currentSymptom.charAt(0).toUpperCase() + currentSymptom.slice(1)}
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="chat-header-right">
          <div className="hipaa-header-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            Privacy Focused
          </div>
          <div className="status-dot-wrapper">
            <span className="status-dot" />
            <span className="status-label">Online</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Main content area */}
      <div className="chat-content-area">
        {/* Chat column */}
        <div className="chat-column">
          <TriageProgressBar />

          {/* Scrollable messages */}
          <div className="messages-scroll" ref={scrollRef}>
            {messages.length === 0 ? (
              /* Empty state / Welcome screen */
              <div className="welcome-screen">
                <div className="welcome-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"
                    fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
                  </svg>
                </div>
                <h2 className="welcome-title">Clinical Decision Support</h2>
                <p className="welcome-desc">
                  Intelligent triage system initialized. Please select a primary presentation below or describe the patient's symptoms to begin structured assessment.
                </p>
                <div className="quick-start-grid">
                  {QUICK_START.map((q) => (
                    <button
                      key={q.label}
                      id={`quick-start-${q.label.replace(/\s+/g, '-').toLowerCase()}`}
                      className="quick-start-btn"
                      onClick={() => handleQuickStart(q.symptom)}
                    >
                      {q.label}
                    </button>
                  ))}
                  <button
                    className="quick-start-btn"
                    onClick={handleOtherSymptom}
                  >
                    <span style={{ opacity: 0.7, marginRight: '4px' }}>+</span> Other Symptom
                  </button>
                </div>
                <p style={{ marginTop: '16px', fontSize: '0.8rem', color: 'var(--text-muted)', opacity: 0.7 }}>
                  You can also describe other symptoms manually.
                </p>
              </div>
            ) : (
              <div className="messages-list">
                {messages.map((msg) => (
                  <MessageBubble key={msg.id} message={msg} />
                ))}
                {isLoading && <TypingIndicator phase={loadingPhase} />}
              </div>
            )}
          </div>

          {/* Input box */}
          <InputBox />
        </div>

        {/* Case summary panel (desktop only, when symptom detected) */}
        {showSummaryPanel && <CaseSummaryPanel />}
      </div>
    </div>
  );
}
