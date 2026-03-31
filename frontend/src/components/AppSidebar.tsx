import { useState } from 'react';
import { useChat } from '../context/ChatContext';

interface SessionItemProps {
  id: string;
  title: string;
  isActive: boolean;
  onSwitch: () => void;
  onDelete: () => void;
}

function SessionItem({ id, title, isActive, onSwitch, onDelete }: SessionItemProps) {
  return (
    <div
      id={`session-${id}`}
      className={`session-item ${isActive ? 'session-active' : ''}`}
      onClick={onSwitch}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && onSwitch()}
      aria-current={isActive ? 'page' : undefined}
    >
      <div className="session-icon">
        <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
      </div>
      <span className="session-title">{title}</span>
      <button
        className="session-delete-btn"
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        aria-label={`Delete session: ${title}`}
        title="Delete"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24"
          fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
}

export function AppSidebar() {
  const { sessions, activeSessionId, createNewSession, switchSession, deleteSession } = useChat();
  const [collapsed, setCollapsed] = useState(false);

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();

  const todaySessions = sessions.filter((s) => s.createdAt >= today);
  const previousSessions = sessions.filter((s) => s.createdAt < today);

  return (
    <aside className={`app-sidebar ${collapsed ? 'sidebar-collapsed' : ''}`} aria-label="Navigation sidebar">
      {/* Header */}
      <div className="sidebar-header">
        {!collapsed && (
          <div className="sidebar-brand">
            <div className="brand-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
              </svg>
            </div>
            <div className="brand-text">
              <span className="brand-name">MedAssist AI</span>
              <span className="brand-tagline">Symptom Triage</span>
            </div>
          </div>
        )}
        {collapsed && (
          <div className="brand-icon-only">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
        )}
        <button
          id="sidebar-toggle-btn"
          className="sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          title={collapsed ? 'Expand' : 'Collapse'}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            {collapsed
              ? <><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="18" x2="21" y2="18" /></>
              : <><line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="15" y2="12" /><line x1="3" y1="18" x2="21" y2="18" /></>
            }
          </svg>
        </button>
      </div>

      {/* New Consultation Button */}
      <div className="sidebar-new-btn-wrapper">
        <button
          id="new-consultation-btn"
          className={`new-consultation-btn ${collapsed ? 'btn-icon-only' : ''}`}
          onClick={createNewSession}
          title="New Consultation"
          aria-label="Start new consultation"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
            fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          {!collapsed && <span>New Consultation</span>}
        </button>
      </div>

      {/* Session List */}
      {!collapsed && (
        <nav className="sidebar-sessions" aria-label="Consultation history">
          {todaySessions.length > 0 && (
            <div className="session-group">
              <span className="session-group-label">Today</span>
              {todaySessions.map((s) => (
                <SessionItem
                  key={s.id}
                  id={s.id}
                  title={s.title}
                  isActive={s.id === activeSessionId}
                  onSwitch={() => switchSession(s.id)}
                  onDelete={() => deleteSession(s.id)}
                />
              ))}
            </div>
          )}
          {previousSessions.length > 0 && (
            <div className="session-group">
              <span className="session-group-label">Previous</span>
              {previousSessions.map((s) => (
                <SessionItem
                  key={s.id}
                  id={s.id}
                  title={s.title}
                  isActive={s.id === activeSessionId}
                  onSwitch={() => switchSession(s.id)}
                  onDelete={() => deleteSession(s.id)}
                />
              ))}
            </div>
          )}
          {sessions.length === 0 && (
            <p className="no-sessions">No consultations yet</p>
          )}
        </nav>
      )}

      {/* Footer */}
      <div className={`sidebar-footer ${collapsed ? 'footer-collapsed' : ''}`}>
        {!collapsed && (
          <p className="sidebar-disclaimer">
            For informational purposes only. Not a substitute for professional medical advice.
          </p>
        )}
      </div>
    </aside>
  );
}
