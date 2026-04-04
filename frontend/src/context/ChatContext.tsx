import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type Dispatch,
  type SetStateAction,
} from 'react';
import type { CaseSummary, LoadingPhase, Message, Session, TriageProgress } from '../types';
import {
  detectSymptom,
  getTriageStateInternal,
  SYMPTOM_TITLE_MAP,
} from '../engine/simulation-engine';

function uuid() {
  return crypto.randomUUID();
}

function createSession(): Session {
  return { id: uuid(), title: 'New Consultation', messages: [], createdAt: Date.now() };
}

interface ChatContextValue {
  sessions: Session[];
  activeSessionId: string;
  messages: Message[];
  isLoading: boolean;
  loadingPhase: LoadingPhase;
  triageProgress: TriageProgress;
  caseSummary: CaseSummary;
  sendMessage: (content: string) => Promise<void>;
  createNewSession: () => void;
  switchSession: (id: string) => void;
  deleteSession: (id: string) => void;
  inputValue: string;
  setInputValue: Dispatch<SetStateAction<string>>;
  isCustomInput: boolean;
  setIsCustomInput: Dispatch<SetStateAction<boolean>>;
}

const ChatContext = createContext<ChatContextValue | null>(null);

function loadSessions(): Session[] {
  try {
    const raw = localStorage.getItem('medassist-sessions');
    if (raw) return JSON.parse(raw) as Session[];
  } catch { /* ignore */ }
  return [];
}

function loadActiveId(sessions: Session[]): string {
  const stored = localStorage.getItem('medassist-active-session');
  if (stored && sessions.find((s) => s.id === stored)) return stored;
  return sessions[0]?.id ?? '';
}

export function ChatProvider({ children }: { children: ReactNode }) {
  const initialSessions = useMemo(() => {
    const s = loadSessions();
    if (s.length === 0) return [createSession()];
    return s;
  }, []);

  const [sessions, setSessions] = useState<Session[]>(initialSessions);
  const [activeSessionId, setActiveSessionId] = useState<string>(() => loadActiveId(initialSessions));
  const [isLoading, setIsLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState<LoadingPhase>(null);
  const [inputValue, setInputValue] = useState('');
  const [isCustomInput, setIsCustomInput] = useState(false);
  const abortRef = useRef(false);

  // Persist sessions
  useEffect(() => {
    localStorage.setItem('medassist-sessions', JSON.stringify(sessions));
  }, [sessions]);

  // Persist active session
  useEffect(() => {
    localStorage.setItem('medassist-active-session', activeSessionId);
  }, [activeSessionId]);

  const messages = useMemo(
    () => sessions.find((s) => s.id === activeSessionId)?.messages ?? [],
    [sessions, activeSessionId]
  );

  const updateSession = useCallback(
    (id: string, updater: (s: Session) => Session) => {
      setSessions((prev) => prev.map((s) => (s.id === id ? updater(s) : s)));
    },
    []
  );

  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      const userMsg: Message = {
        id: uuid(),
        role: 'user',
        content: content.trim(),
        timestamp: Date.now(),
      };

      const sessionId = activeSessionId;
      let currentMessages: Message[] = [];

      updateSession(sessionId, (s) => {
        const updated = { ...s, messages: [...s.messages, userMsg] };
        // Auto-title on first message
        if (s.messages.length === 0) {
          const sym = detectSymptom(content);
          updated.title = sym
            ? SYMPTOM_TITLE_MAP[sym] ?? 'New Consultation'
            : content.trim().slice(0, 30) + (content.length > 30 ? '…' : '');
        }
        currentMessages = updated.messages;
        return updated;
      });

      setIsLoading(true);
      abortRef.current = false;

      try {
        setLoadingPhase('analyzing');
        const response = await fetch("http://127.0.0.1:8000/api/v1/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            message: content,
            session_id: sessionId,
            history: currentMessages.slice(0, -1).map(m => ({ role: m.role, content: m.content }))
          })
        });

        if (!response.ok) {
           throw new Error(`API error: ${response.status}`);
        }

        setLoadingPhase('generating');
        const data = await response.json();
        
        // STEP 4: MANDATORY DEBUG LOGS
        console.log("API RESPONSE:", data);
        console.log("RAW RESPONSE TEXT:", data.response);

        if (abortRef.current) return;

        const assistantMsg: Message = {
          id: uuid(),
          role: 'assistant',
          content: data.response, // STEP 3: Map backend 'response' field
          timestamp: Date.now(),
          status: data.status,
          classification: data.status === 'ASK' ? 'triage' : 'insight',
          meta: data.meta || {
            symptom: 'unknown',
            progress: '0/0'
          }
        };

        updateSession(sessionId, (s) => ({
          ...s,
          messages: [...s.messages, assistantMsg],
        }));
      } catch (err) {
        // STEP 5: Error Handling
        console.error("API ERROR:", err);
        const errorMsg: Message = {
          id: uuid(),
          role: 'assistant',
          content: "I encountered a connection error. Please ensure the backend server is running and try again.",
          timestamp: Date.now(),
          classification: 'general'
        };
        updateSession(sessionId, (s) => ({
          ...s,
          messages: [...s.messages, errorMsg],
        }));
      } finally {
        if (!abortRef.current) {
          setIsLoading(false);
          setLoadingPhase(null);
        }
      }
    },
    [activeSessionId, isLoading, updateSession]
  );

  const createNewSession = useCallback(() => {
    abortRef.current = true;
    setIsLoading(false);
    setLoadingPhase(null);
    const newSession = createSession();
    setSessions((prev) => [newSession, ...prev]);
    setActiveSessionId(newSession.id);
  }, []);

  const switchSession = useCallback((id: string) => {
    abortRef.current = true;
    setIsLoading(false);
    setLoadingPhase(null);
    setActiveSessionId(id);
  }, []);

  const deleteSession = useCallback(
    (id: string) => {
      setSessions((prev) => {
        const filtered = prev.filter((s) => s.id !== id);
        if (filtered.length === 0) {
          const fresh = createSession();
          setActiveSessionId(fresh.id);
          return [fresh];
        }
        if (id === activeSessionId) {
          setActiveSessionId(filtered[0].id);
        }
        return filtered;
      });
    },
    [activeSessionId]
  );

  // Derived: triage progress
  const triageProgress = useMemo((): TriageProgress => {
    const state = getTriageStateInternal(messages);
    return {
      detectedSymptom: state.detectedSymptom,
      answeredCount: state.answeredCount,
      totalQuestions: state.totalQuestions,
      isComplete: state.totalQuestions > 0 && state.answeredCount >= state.totalQuestions,
      collectedData: state.collectedData,
    };
  }, [messages]);

  // Derived: case summary
  const caseSummary = useMemo((): CaseSummary => {
    const { detectedSymptom, collectedData } = triageProgress;
    const notes: string[] = [];

    if (detectedSymptom === 'headache') {
      if (collectedData['location']) notes.push(`Location: ${collectedData['location']}`);
    }
    if (detectedSymptom === 'chest pain') {
      if (collectedData['radiation']) notes.push(`Radiation: ${collectedData['radiation']}`);
    }
    if (detectedSymptom === 'abdominal pain') {
      if (collectedData['location']) notes.push(`Location: ${collectedData['location']}`);
    }

    return {
      symptom: detectedSymptom
        ? detectedSymptom.charAt(0).toUpperCase() + detectedSymptom.slice(1)
        : null,
      duration: collectedData['duration'] ?? null,
      severity: collectedData['severity'] ?? null,
      temperature: collectedData['temperature'] ?? null,
      otherSymptoms: collectedData['other_symptoms'] ?? collectedData['associated'] ?? null,
      additionalNotes: notes,
    };
  }, [triageProgress]);

  return (
    <ChatContext.Provider
      value={{
        sessions,
        activeSessionId,
        messages,
        isLoading,
        loadingPhase,
        triageProgress,
        caseSummary,
        sendMessage,
        createNewSession,
        switchSession,
        deleteSession,
        inputValue,
        setInputValue,
        isCustomInput,
        setIsCustomInput,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const ctx = useContext(ChatContext);
  if (!ctx) throw new Error('useChat must be used within ChatProvider');
  return ctx;
}
