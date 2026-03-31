import { useCallback, useEffect, useRef, useState } from 'react';
import { useChat } from '../context/ChatContext';

export function InputBox() {
  const { sendMessage, isLoading, inputValue, setInputValue, isCustomInput } = useChat();
  const [isListening, setIsListening] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const recognitionRef = useRef<any | null>(null);

  // Auto-focus when loading ends
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus();
    }
  }, [isLoading]);

  // Auto-resize textarea
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    const el = e.target;
    el.style.height = '44px';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  };

  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;
    const msg = inputValue.trim();
    setInputValue('');
    if (inputRef.current) {
      inputRef.current.style.height = '44px';
    }
    await sendMessage(msg);
  }, [inputValue, isLoading, sendMessage, setInputValue]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // ─── Voice Input ──────────────────────────────────────────────────────────
  const toggleVoice = () => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognitionRef.current = recognition;
    recognition.lang = 'en-US';
    recognition.interimResults = true;
    recognition.continuous = false;

    recognition.onstart = () => setIsListening(true);
    recognition.onend = () => setIsListening(false);
    recognition.onerror = () => setIsListening(false);

    recognition.onresult = (event: any) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setInputValue((prev: string) => {
        const combined = (prev + ' ' + transcript).trim();
        // Auto-resize
        setTimeout(() => {
          if (inputRef.current) {
            inputRef.current.style.height = '44px';
            inputRef.current.style.height =
              Math.min(inputRef.current.scrollHeight, 120) + 'px';
          }
        }, 0);
        return combined;
      });
    };

    recognition.start();
  };

  return (
    <div className="input-box-wrapper">
      <div className="input-box-inner">
        <div className="textarea-row">
          <textarea
            id="chat-input"
            ref={inputRef}
            className="chat-textarea"
            placeholder={isLoading ? 'Waiting for response…' : (isCustomInput ? 'Describe your symptom (e.g., dizziness, nausea, fatigue)' : 'Describe your symptoms…')}
            value={inputValue}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            rows={1}
            aria-label="Symptom description input"
          />

          {/* Voice Button */}
          <button
            id="voice-input-btn"
            className={`icon-btn voice-btn ${isListening ? 'voice-active' : ''}`}
            onClick={toggleVoice}
            disabled={isLoading}
            title={isListening ? 'Stop listening' : 'Voice input'}
            aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
          >
            {isListening ? (
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                fill="currentColor" stroke="none">
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
                fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            )}
            {isListening && <span className="voice-pulse" />}
          </button>

          {/* Send Button */}
          <button
            id="send-btn"
            className="send-btn"
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
            aria-label="Send message"
            title="Send (Enter)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>

        <div className="input-footer">
          <span className="input-hint">
            <kbd>Enter</kbd> to send · <kbd>Shift+Enter</kbd> for new line
            {isListening && <span className="listening-label"> · 🎙 Listening…</span>}
          </span>
          <span className="hipaa-badge">
            <svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" viewBox="0 0 24 24"
              fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            Privacy Focused
          </span>
        </div>
      </div>
    </div>
  );
}
