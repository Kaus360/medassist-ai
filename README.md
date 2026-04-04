# 🏥 MedAssist AI

A safety-critical AI-powered clinical triage system designed to assess symptoms through structured questioning while enforcing strict medical safety constraints.

---

## 🚀 Live Flow

1. User enters symptom (e.g., Chest pain)
2. System performs step-by-step triage (type, duration, severity, etc.)
3. Once sufficient data is collected → AI generates structured guidance
4. Safety layer filters unsafe outputs (no prescriptions/dosage)

---

## 🧠 Key Innovation

Unlike typical AI chatbots, this system focuses on **controlling AI behavior** instead of blindly trusting model outputs.

It implements:
- Multi-layer safety enforcement
- Stateful triage (not stateless chat)
- Multi-LLM failover (Gemini → Groq → OpenRouter)
- Adversarial input protection
- Audit logging for reliability

---

## 🏗️ Architecture
# 🏥 MedAssist AI

A safety-critical AI-powered clinical triage system designed to assess symptoms through structured questioning while enforcing strict medical safety constraints.

---

## 🚀 Live Flow

1. User enters symptom (e.g., Chest pain)
2. System performs step-by-step triage (type, duration, severity, etc.)
3. Once sufficient data is collected → AI generates structured guidance
4. Safety layer filters unsafe outputs (no prescriptions/dosage)

---

## 🧠 Key Innovation

Unlike typical AI chatbots, this system focuses on **controlling AI behavior** instead of blindly trusting model outputs.

It implements:
- Multi-layer safety enforcement
- Stateful triage (not stateless chat)
- Multi-LLM failover (Gemini → Groq → OpenRouter)
- Adversarial input protection
- Audit logging for reliability

---

## 🏗️ Architecture
User
↓
Triage Agent (Stateful)
↓
LLM Manager (Failover)
↓
Safety Filter (Critical Layer)
↓
Final Response


---

## 🛡️ Safety Features

- Blocks prescriptions and dosage instructions
- Prevents unsafe medical claims
- Enforces mandatory disclaimer
- Logs raw vs filtered outputs
- Handles adversarial inputs

---

## 🧪 Example Flow

**Input:**
Chest pain → pressure → 1 day → severe → no other symptoms

**Output:**
- Structured clinical summary
- Possible causes
- Safe recommendations
- Red flags for escalation

---

## ⚙️ Tech Stack

- FastAPI (Backend)
- React + Vite (Frontend)
- Multi-LLM Integration (Gemini, Groq, OpenRouter)
- Custom Safety Layer
- JSON-based Memory System

---

## ⚠️ Disclaimer

This system is not a substitute for professional medical advice.
