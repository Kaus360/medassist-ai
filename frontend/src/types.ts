export type Classification = 'triage' | 'insight' | 'general';
export type LoadingPhase = 'analyzing' | 'generating' | null;
export type Theme = 'light' | 'dark';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  classification?: Classification;
  severity?: SeverityLevel;
  status?: 'ASK' | 'PROCEED';
  meta?: {
    symptom: string;
    progress: string;
  };
}

export type SeverityLevel = 'low' | 'moderate' | 'high' | 'critical' | null;

export interface Session {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
}

export interface TriageProgress {
  detectedSymptom: string | null;
  answeredCount: number;
  totalQuestions: number;
  isComplete: boolean;
  collectedData: Record<string, string>;
}

export interface CaseSummary {
  symptom: string | null;
  duration: string | null;
  severity: string | null;
  temperature: string | null;
  otherSymptoms: string | null;
  additionalNotes: string[];
}
