import type { LoadingPhase } from '../types';

interface Props {
  phase: LoadingPhase;
}

export function TypingIndicator({ phase }: Props) {
  const label =
    phase === 'analyzing'
      ? 'Analyzing symptoms…'
      : phase === 'generating'
      ? 'Generating triage questions…'
      : 'Processing…';

  return (
    <div className="typing-indicator-wrapper" aria-live="polite" aria-label={label}>
      <div className="avatar assistant-avatar">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
        </svg>
      </div>
      <div className="typing-bubble">
        <span className="typing-label">{label}</span>
        <div className="typing-dots">
          <span className="dot dot-1" />
          <span className="dot dot-2" />
          <span className="dot dot-3" />
        </div>
      </div>
    </div>
  );
}
