import type { Classification, Message, SeverityLevel } from '../types';

// ─── Safety Disclaimer ───────────────────────────────────────────────────────
export const SAFETY_DISCLAIMER =
  '\n\n⚠️ *This system is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the guidance of your physician or other qualified health provider with any questions you may have regarding a medical condition.*';

// ─── Symptom Detection ───────────────────────────────────────────────────────
const SYMPTOM_ALIASES: Record<string, string> = {
  fever: 'fever',
  temperature: 'fever',
  hot: 'fever',
  chills: 'fever',
  headache: 'headache',
  head: 'headache',
  migraine: 'headache',
  'chest pain': 'chest pain',
  chest: 'chest pain',
  'heart pain': 'chest pain',
  'breathing difficulty': 'breathing difficulty',
  breath: 'breathing difficulty',
  breathing: 'breathing difficulty',
  breathless: 'breathing difficulty',
  'shortness of breath': 'breathing difficulty',
  dyspnea: 'breathing difficulty',
  'abdominal pain': 'abdominal pain',
  stomach: 'abdominal pain',
  belly: 'abdominal pain',
  abdomen: 'abdominal pain',
  'stomach ache': 'abdominal pain',
  'stomach pain': 'abdominal pain',
};

export function detectSymptom(text: string): string | null {
  const lower = text.toLowerCase();
  for (const [alias, symptom] of Object.entries(SYMPTOM_ALIASES)) {
    if (lower.includes(alias)) return symptom;
  }
  return null;
}

// ─── Symptom Title Map ───────────────────────────────────────────────────────
export const SYMPTOM_TITLE_MAP: Record<string, string> = {
  fever: 'Fever Consultation',
  headache: 'Headache Case',
  'chest pain': 'Chest Pain Assessment',
  'breathing difficulty': 'Respiratory Assessment',
  'abdominal pain': 'Abdominal Pain Case',
};

// ─── Triage Questions ────────────────────────────────────────────────────────
interface TriageQuestion {
  key: string;
  question: string;
}

const TRIAGE_QUESTIONS: Record<string, TriageQuestion[]> = {
  fever: [
    { key: 'duration', question: 'How long have you had this fever? (e.g., 1 day, 3 days, a week)' },
    { key: 'temperature', question: 'What is your current temperature reading? (if measured, e.g., 101°F / 38.3°C)' },
    { key: 'other_symptoms', question: 'Are you experiencing any other symptoms such as chills, body aches, or sore throat?' },
  ],
  headache: [
    { key: 'location', question: 'Where is the headache located? (frontal/temporal/occipital/diffuse/all over)' },
    { key: 'severity', question: 'On a scale of 1–10, how severe is the headache?' },
    { key: 'duration', question: 'How long have you had this headache, and is it constant or comes and goes?' },
  ],
  'chest pain': [
    { key: 'nature', question: 'How would you describe the chest pain? (sharp / dull / pressure / burning / squeezing)' },
    { key: 'radiation', question: 'Does the pain radiate to your arm, jaw, neck, or back?' },
    { key: 'associated', question: 'Are you experiencing any associated symptoms like shortness of breath, sweating, or nausea?' },
  ],
  'breathing difficulty': [
    { key: 'onset', question: 'When did the breathing difficulty start, and was the onset sudden or gradual?' },
    { key: 'pattern', question: 'Is the breathing difficulty constant or does it come and go? Does it worsen with activity?' },
    { key: 'history', question: 'Do you have any history of asthma, COPD, allergies, or other respiratory conditions?' },
  ],
  'abdominal pain': [
    { key: 'location', question: 'Where exactly in your abdomen is the pain? (upper/lower/left/right/around the navel)' },
    { key: 'pattern', question: 'Is the pain constant or does it come and go? Does anything make it better or worse?' },
    { key: 'associated', question: 'Are you experiencing nausea, vomiting, diarrhea, constipation, or changes in bowel habits?' },
  ],
};

// ─── Clinical Responses ──────────────────────────────────────────────────────
const CLINICAL_RESPONSES: Record<string, string> = {
  fever: `Based on your symptoms, here is a structured clinical assessment:

1. **Monitor Temperature Regularly** – Check every 4–6 hours. Seek immediate care if temperature exceeds 103°F (39.4°C).
2. **Stay Hydrated** – Drink plenty of fluids (water, clear broths, electrolyte drinks) to prevent dehydration from fever sweating.
3. **Rest & Recovery** – Adequate rest supports your immune system. Avoid strenuous activities.
4. **Consider OTC Medications** – Acetaminophen (Tylenol) or ibuprofen (Advil) can help manage fever. Follow dosage instructions.
5. **Watch for Red Flags** – Seek emergency care immediately for: severe headache with stiff neck, difficulty breathing, chest pain, confusion, or rash.
6. **Isolate if Infectious** – If a viral infection is suspected, limit contact with vulnerable individuals.`,

  headache: `Based on your headache description, here is a clinical assessment:

1. **Identify Headache Type** – Based on your description, this may be a tension-type or migraine headache. Pattern and location are key indicators.
2. **Pain Management** – OTC analgesics (ibuprofen, aspirin, or acetaminophen) may provide relief. For migraines, consider triptans if prescribed.
3. **Hydration & Rest** – Dehydration and poor sleep are common headache triggers. Ensure 8 glasses of water daily.
4. **Reduce Triggers** – Common triggers include bright lights, loud noise, stress, caffeine withdrawal, and certain foods.
5. **Posture & Ergonomics** – Tension headaches are often linked to neck/shoulder tension from poor posture.
6. **Red Flags for Emergency** – Sudden "thunderclap" headache, headache with fever + stiff neck, headache after head injury, or visual disturbances require immediate evaluation.`,

  'chest pain': `Based on your chest pain description, here is an urgent clinical assessment:

1. **Rule Out Cardiac Emergency First** – Chest pain with radiation to arm/jaw, sweating, or nausea is a medical emergency. Call emergency services (911) immediately if present.
2. **Rest & Positioning** – Sit or lie in a comfortable position. Avoid physical exertion until evaluated.
3. **Aspirin Consideration** – If cardiac cause is suspected and you are not allergic, chewing 325mg aspirin may be advised (consult emergency services).
4. **Document Symptoms** – Note exact location, quality (sharp/dull/pressure), timing, and any aggravating or relieving factors for the examining physician.
5. **Monitor Vitals** – Track heart rate, breathing rate, and blood pressure if possible.
6. **Seek Immediate Evaluation** – Chest pain should never be self-managed without medical evaluation. This is a priority symptom.`,

  'breathing difficulty': `Based on your breathing difficulty, here is a structured clinical response:

1. **Immediate Positioning** – Sit upright or slightly forward (tripod position) to ease breathing mechanics.
2. **Check Oxygen Support** – If available, a pulse oximeter reading below 94% SpO2 warrants urgent evaluation.
3. **Identify Triggers** – Allergens, exertion, cold air, or anxiety can trigger episodes. Remove yourself from triggers.
4. **Bronchodilator Use** – If prescribed an inhaler (e.g., albuterol), use as directed. Do not exceed prescribed doses.
5. **Call Emergency Services** – Severe shortness of breath, cyanosis (blue lips/fingertips), or inability to speak in full sentences = 911.
6. **Breathing Technique** – Pursed-lip breathing (breathe in through nose, out slowly through pursed lips) can reduce anxiety-driven dyspnea.`,

  'abdominal pain': `Based on your abdominal pain description, here is a clinical assessment:

1. **Characterize the Pain** – Location, severity, and pattern help indicate organ involvement (e.g., right lower quadrant pain may suggest appendicitis).
2. **Dietary Management** – Avoid solid food temporarily. Clear fluids and bland diet (BRAT: bananas, rice, applesauce, toast) may ease symptoms.
3. **Monitor for Escalation** – Pain that worsens rapidly, extends to the back, or is accompanied by high fever requires urgent evaluation.
4. **Avoid Analgesics Initially** – Taking pain relievers before diagnosis may mask important clinical signs.
5. **Assess for Appendicitis Signs** – Pain migrating to right lower abdomen, rebound tenderness, and loss of appetite = seek care urgently.
6. **Hydration** – Especially important if nausea, vomiting, or diarrhea is present to prevent dehydration.`,
};

// ─── Severity Assessment ─────────────────────────────────────────────────────
function assessSeverity(symptom: string, collectedData: Record<string, string>): SeverityLevel {
  if (!symptom) return null;

  if (symptom === 'chest pain') {
    const associated = collectedData['associated'] || '';
    const radiation = collectedData['radiation'] || '';
    if (
      associated.toLowerCase().includes('shortness') ||
      associated.toLowerCase().includes('sweat') ||
      radiation.toLowerCase().includes('arm') ||
      radiation.toLowerCase().includes('jaw')
    ) return 'critical';
    return 'high';
  }

  if (symptom === 'breathing difficulty') {
    const onset = collectedData['onset'] || '';
    if (onset.toLowerCase().includes('sudden')) return 'critical';
    return 'high';
  }

  if (symptom === 'fever') {
    const temp = collectedData['temperature'] || '';
    const tempNum = parseFloat(temp.replace(/[^0-9.]/g, ''));
    if (tempNum >= 103 || temp.toLowerCase().includes('high')) return 'high';
    if (tempNum >= 101) return 'moderate';
    return 'low';
  }

  if (symptom === 'headache') {
    const severity = collectedData['severity'] || '';
    const sevNum = parseInt(severity.replace(/[^0-9]/g, ''));
    if (sevNum >= 8) return 'high';
    if (sevNum >= 5) return 'moderate';
    return 'low';
  }

  if (symptom === 'abdominal pain') {
    const associated = collectedData['associated'] || '';
    if (associated.toLowerCase().includes('vomit') || associated.toLowerCase().includes('blood')) return 'high';
    return 'moderate';
  }

  return 'low';
}

// ─── Internal Triage State ───────────────────────────────────────────────────
interface TriageState {
  detectedSymptom: string | null;
  answeredCount: number;
  totalQuestions: number;
  collectedData: Record<string, string>;
}

export function getTriageStateInternal(history: Message[]): TriageState {
  let detectedSymptom: string | null = null;
  const collectedData: Record<string, string> = {};

  // Detect symptom from assistant messages first (more reliable)
  for (const msg of history) {
    if (msg.role === 'assistant' && msg.classification === 'triage') {
      for (const [sym, questions] of Object.entries(TRIAGE_QUESTIONS)) {
        for (const q of questions) {
          if (msg.content.includes(q.question.substring(0, 30))) {
            detectedSymptom = sym;
            break;
          }
        }
        if (detectedSymptom) break;
      }
    }
    if (detectedSymptom) break;
  }

  // Fallback: scan user messages
  if (!detectedSymptom) {
    for (const msg of history) {
      if (msg.role === 'user') {
        const sym = detectSymptom(msg.content);
        if (sym) { detectedSymptom = sym; break; }
      }
    }
  }

  if (!detectedSymptom) {
    return { detectedSymptom: null, answeredCount: 0, totalQuestions: 0, collectedData };
  }

  const questions = TRIAGE_QUESTIONS[detectedSymptom] || [];
  let answeredCount = 0;

  // Track answered questions by looking for Q→UserReply pairs
  for (let i = 0; i < history.length - 1; i++) {
    const msg = history[i];
    if (msg.role === 'assistant' && msg.classification === 'triage') {
      const matchedQ = questions.find((q) => msg.content.includes(q.question.substring(0, 30)));
      if (matchedQ) {
        // Look for next user message
        const nextUser = history.slice(i + 1).find((m) => m.role === 'user');
        if (nextUser) {
          collectedData[matchedQ.key] = nextUser.content;
          answeredCount++;
        }
      }
    }
  }

  return {
    detectedSymptom,
    answeredCount,
    totalQuestions: questions.length,
    collectedData,
  };
}

// ─── Triage Simulation ───────────────────────────────────────────────────────
interface SimulationResult {
  content: string;
  classification: Classification;
  severity?: SeverityLevel;
  status: 'ASK' | 'PROCEED';
  meta: {
    symptom: string;
    progress: string;
  };
}

export function simulateTriage(input: string, history: Message[]): SimulationResult {
  const state = getTriageStateInternal(history);

  if (state.detectedSymptom) {
    const questions = TRIAGE_QUESTIONS[state.detectedSymptom];
    if (state.answeredCount < state.totalQuestions) {
      const nextQ = questions[state.answeredCount];
      const content =
        `To properly assess your **${state.detectedSymptom}**, I need a few more details.\n\n${nextQ.question}` +
        SAFETY_DISCLAIMER;
      return { 
        content, classification: 'triage', status: 'ASK', 
        meta: { symptom: state.detectedSymptom, progress: `${state.answeredCount + 1}/${state.totalQuestions}` } 
      };
    } else {
      // All questions answered — generate clinical response
      const clinical = CLINICAL_RESPONSES[state.detectedSymptom] || 'Thank you for sharing your symptoms. Please consult a healthcare provider for a complete evaluation.';
      const severity = assessSeverity(state.detectedSymptom, state.collectedData);
      return { 
        content: clinical + SAFETY_DISCLAIMER, classification: 'insight', severity, status: 'PROCEED',
        meta: { symptom: state.detectedSymptom, progress: `${state.totalQuestions}/${state.totalQuestions}` }
      };
    }
  }

  // No prior symptom — try detecting from current input
  const newSymptom = detectSymptom(input);
  if (newSymptom) {
    const questions = TRIAGE_QUESTIONS[newSymptom];
    const firstQ = questions[0];
    const content =
      `I understand you're experiencing **${newSymptom}**. Let me help assess your condition.\n\n${firstQ.question}` +
      SAFETY_DISCLAIMER;
    return { 
      content, classification: 'triage', status: 'ASK',
      meta: { symptom: newSymptom, progress: `1/${questions.length}` }
    };
  }

  // General prompt (Step 2: REMOVE FALLBACK RESET)
  // Only allow this if no session exists AND no symptom was detected in current input.
  const content = state.detectedSymptom 
    ? `I didn't quite understand that. Please provide more detail about your **${state.detectedSymptom}** so I can help.`
    : `Enter your primary symptom to begin triage.`;

  return { 
    content, classification: 'general', status: 'ASK',
    meta: { symptom: state.detectedSymptom || 'unknown', progress: '0/0' }
  };
}

// ─── Async Response Simulator ─────────────────────────────────────────────────
export async function simulateResponse(
  input: string,
  history: Message[],
  onPhase: (phase: 'analyzing' | 'generating') => void
): Promise<SimulationResult> {
  onPhase('analyzing');
  await delay(600 + Math.random() * 400);
  onPhase('generating');
  await delay(400 + Math.random() * 400);
  return simulateTriage(input, history);
}

function delay(ms: number) {
  return new Promise((res) => setTimeout(res, ms));
}

// ─── Derived State Helpers ────────────────────────────────────────────────────
export { TRIAGE_QUESTIONS };
