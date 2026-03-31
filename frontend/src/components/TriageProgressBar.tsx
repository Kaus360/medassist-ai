import { useMemo } from 'react';
import { useChat } from '../context/ChatContext';

export function TriageProgressBar() {
  const { messages } = useChat();

  if (messages.length === 0) return null;

  const currentSymptom = useMemo(() => {
    const lastBot = [...messages].reverse().find(m => m.role === 'assistant');
    return lastBot?.meta?.symptom || 'unknown';
  }, [messages]);

  const currentProgress = useMemo(() => {
    const lastBot = [...messages].reverse().find(m => m.role === 'assistant');
    return lastBot?.meta?.progress || '0/0';
  }, [messages]);

  const rawSymptom = currentSymptom === 'unknown' ? 'General Assessment' : `${currentSymptom.charAt(0).toUpperCase() + currentSymptom.slice(1)} Assessment`;

  const [answeredStr, totalStr] = currentProgress.split('/');
  const answeredCount = parseInt(answeredStr) || 0;
  const totalQuestions = parseInt(totalStr) || 0;
  
  const pct = totalQuestions > 0 ? (answeredCount / totalQuestions) * 100 : 0;
  const isComplete = totalQuestions > 0 && answeredCount >= totalQuestions;

  const isEmergency = currentSymptom === 'chest pain' || currentSymptom === 'breathing difficulty';

  return (
    <div className="triage-progress-bar" style={isEmergency ? { borderBottom: '1px solid hsl(0, 70%, 50%, 0.3)', backgroundColor: 'hsl(0, 70%, 50%, 0.02)' } : {}}>
      <div className="triage-progress-left">
        <span className="progress-label">Triage Stage:</span>
        <span className="symptom-badge" style={isEmergency ? { borderColor: 'hsl(0, 70%, 50%, 0.4)', color: 'var(--medical-critical)' } : {}}>
          {isEmergency && <span style={{ marginRight: '4px' }}>⚠️</span>}
          {rawSymptom} {totalQuestions > 0 ? `(Step ${currentProgress})` : ''}
        </span>
      </div>

      {totalQuestions > 0 && (
        <div className="triage-progress-right">
          <div className="progress-track" style={{ width: '100px' }}>
            <div
              className={`progress-fill ${isComplete ? 'fill-complete' : 'fill-inprogress'}`}
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
