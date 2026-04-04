"""
backend/services/safety_filter.py

Advanced, production-grade Safety Filter for MedAssist AI.
Upgraded with improved spaced digit collapse and semantic word-based number detection.
"""

import re
from typing import Dict, List

from backend.services.safety_logger import SafetyLogger


class SafetyFilter:
    """
    A production-quality safety filter for sanitizing clinical assistant output.
    Processes text via normalization, word-to-number conversion, and sentence splitting.
    """

    def __init__(self) -> None:
        """Initialize the filter and compile patterns for performance."""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Initialize all regex patterns with optimized anchoring and boundaries."""
        
        # 1. Dosage patterns (units, frequency, intervals)
        self.DOSAGE_UNITS = re.compile(
            r"\b\d+\s*(mg|g|ml|tablets?|capsules?|drops?)\b", 
            re.IGNORECASE
        )
        self.DOSAGE_FREQUENCY = re.compile(
            r"\b\d+\s*times?\s*(a|per)?\s*(day|week)|"
            r"twice\s+daily|once\s+nightly|"
            r"daily|per\s+day|each\s+day\b", 
            re.IGNORECASE
        )
        self.DOSAGE_INTERVAL = re.compile(
            r"\bevery\s*\d+\s*(hours?|days?)\b", 
            re.IGNORECASE
        )

        # 2. Prescription patterns (instructional intent)
        self.PRESCRIPTION_INTENT = re.compile(
            r"\b(start|begin|use|apply|consume|take)\b(?!\s+(?:care|your time|a break|deep|into))|"
            r"\brecommended\s+treatment\s+is|"
            r"\byou\s+need\s+to\s+take|"
            r"\bbest\s+medicine\s+is",
            re.IGNORECASE
        )

        # 3. Medical Authority patterns (implicit or explicit claims)
        self.MEDICAL_AUTHORITY = re.compile(
            r"\bas\s+a\s+doctor|"
            r"\bclinically\s+recommended|"
            r"\bstandard\s+treatment|"
            r"\bfirst-line\s+treatment|"
            r"\bI\s+suggest\s+you\s+take|"
            r"\bmy\s+diagnosis\s+is|"
            r"\bI\s+prescribe",
            re.IGNORECASE
        )

    def _normalize_text(self, text: str) -> str:
        """
        Normalize input text for consistent regex matching.
        Handles separator normalization and robust spaced digit collapse.
        """
        if not text:
            return ""
        
        # Lowercase for consistency
        normalized = text.lower()
        
        # A. Normalize separators (hyphens/underscores to spaces)
        normalized = normalized.replace("-", " ").replace("_", " ")

        # B. Robust collapse of spaced numbers (e.g., "5 0 0" -> "500")
        # Matches a digit followed by space(s) and another digit
        normalized = re.sub(r'(\d)\s+(?=\d)', r'\1', normalized)

        # Standardize spacing for units (e.g., 500mg -> 500 mg)
        normalized = re.sub(r'(\d+)\s*([a-zA-Z]+)', r'\1 \2', normalized)
        
        # Collapse multiple spaces and trim
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized

    def _convert_word_numbers(self, text: str) -> str:
        """
        Convert written-out numbers (e.g., 'five') to digits.
        Handles basic units and 'hundred' patterns.
        """
        word_map = {
            "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
            "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
            "ten": "10"
        }
        
        result = text
        for word, num in word_map.items():
            result = re.sub(r'\b' + word + r'\b', num, result, flags=re.IGNORECASE)
        
        # Handle "hundred" (e.g., "5 hundred" -> "500", "hundred" -> "100")
        result = re.sub(r'(\d+)\s+hundred\b', r'\1' + "00", result, flags=re.IGNORECASE)
        result = re.sub(r'\bhundred\b', "100", result, flags=re.IGNORECASE)
        
        return result

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into individual sentences for granular processing."""
        # Split on sentence boundaries: . ? ! followed by space or newline
        sentences = re.split(r'(?<=[.!?])\s+|\n', text)
        return [s.strip() for s in sentences if s.strip()]

    def check_unsafe_content(self, text: str) -> Dict[str, bool]:
        """Check text for unsafe segments using normalized and converted pipelines."""
        normalized = self._normalize_text(text)
        semantic = self._convert_word_numbers(normalized)
        
        flags = {
            "has_dosage": bool(
                self.DOSAGE_UNITS.search(semantic) or 
                self.DOSAGE_FREQUENCY.search(semantic) or 
                self.DOSAGE_INTERVAL.search(semantic)
            ),
            "has_prescription": bool(self.PRESCRIPTION_INTENT.search(semantic)),
            "has_medical_claim": bool(self.MEDICAL_AUTHORITY.search(semantic))
        }
        
        return flags

    def sanitize(self, text: str, global_flags: Dict[str, bool]) -> str:
        """
        Sanitize text at a sentence level. Unsafe sentences are replaced or removed.
        Safe sentences are preserved as-is.
        """
        if not text:
            return ""

        sentences = self._split_sentences(text)
        processed_sentences = []

        for sentence in sentences:
            # Prepare sentence for analysis
            norm_s = self._normalize_text(sentence)
            sem_s = self._convert_word_numbers(norm_s)
            
            s_flags = {
                "dosage": bool(
                    self.DOSAGE_UNITS.search(sem_s) or 
                    self.DOSAGE_FREQUENCY.search(sem_s) or 
                    self.DOSAGE_INTERVAL.search(sem_s)
                ),
                "prescription": bool(self.PRESCRIPTION_INTENT.search(sem_s)),
                "authority": bool(self.MEDICAL_AUTHORITY.search(sem_s))
            }

            # Decision Logic:
            # If dosage detected -> REMOVE the full sentence
            if s_flags["dosage"]:
                continue
                
            # If prescription intent -> REPLACE with professional consult message
            if s_flags["prescription"]:
                processed_sentences.append(
                    "Treatment decisions should be made by a qualified medical professional."
                )
                continue
                
            # If medical authority claim -> NEUTRALIZE sentence
            if s_flags["authority"]:
                processed_sentences.append(
                    "Medical guidance varies; consult a professional."
                )
                continue

            # Safe sentence
            processed_sentences.append(sentence)

        return "\n".join(processed_sentences).strip()


    def add_disclaimer(self, text: str) -> str:
        """Append the standard mandatory medical disclaimer."""
        disclaimer = "This system is not a substitute for professional medical advice."
        if not text:
            return disclaimer
        return f"{text.strip()}\n\n{disclaimer}"

    def process(self, text: str, user_input: str = "N/A") -> dict:
        """
        Main entry point for safety processing.
        Ensures the final output is safe and contains a disclaimer.
        Logs the safety event for auditing.
        Returns a structured result instead of a plain string.
        """
        if not text:
            final_output = self.add_disclaimer("")
            flags = {"has_dosage": False, "has_prescription": False, "has_medical_claim": False}
            safety_action = "none"
            
            SafetyLogger.log_event({
                "user_input": user_input,
                "raw_llm_output": "",
                "flags": flags,
                "safety_action": safety_action,
                "final_output": final_output
            })
            return {
                "text": final_output,
                "flags": flags,
                "safety_action": safety_action
            }

        # 1. Baseline analysis
        flags = self.check_unsafe_content(text)
        
        # 2. Granular sentence-level sanitization
        sanitized_text = self.sanitize(text, flags)
        
        # 3. Determine safety_action
        has_flags = any(flags.values())
        if not has_flags:
            safety_action = "none"
        elif not sanitized_text.strip():
            safety_action = "blocked"
        else:
            safety_action = "sanitized"

        # 4. Final disclaimer enforcement
        final_output = self.add_disclaimer(sanitized_text)

        # 5. Formatting Cleanup (Step 2)
        # Normalize multiple horizontal spaces, preserve newlines
        final_output = re.sub(r'[ \t]+', ' ', final_output)
        # Collapse 3+ newlines to 2
        final_output = re.sub(r'\n{3,}', '\n\n', final_output)
        final_output = final_output.strip()

        # 6. Audit logging

        SafetyLogger.log_event({
            "user_input": user_input,
            "raw_llm_output": text,
            "flags": flags,
            "safety_action": safety_action,
            "final_output": final_output
        })

        return {
            "text": final_output,
            "flags": flags,
            "safety_action": safety_action
        }
