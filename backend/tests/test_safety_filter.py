"""
backend/tests/test_safety_filter.py

Validation test suite for MedAssist AI SafetyFilter.
Ensures robust detection and sanitization of unsafe medical advice
across edge cases and formatting variations.
"""

from backend.services.safety_filter import SafetyFilter


def run_test_suite() -> None:
    """Execute the full safety filter test suite and report results."""
    
    sf = SafetyFilter()
    
    cases = [
        # 1. Basic Dosage
        {
            "name": "Basic Dosage",
            "input": "You should take 500mg paracetamol twice daily.",
            "checks": [
                lambda out: "500mg" not in out,
                lambda out: "twice daily" not in out,
                lambda out: "not a substitute for professional medical advice" in out.lower()
            ]
        },
        # 2. Spaced Dosage Attack
        {
            "name": "Spaced Dosage",
            "input": "Take 5 0 0 mg of ibuprofen.",
            "checks": [
                lambda out: "5 0 0 mg" not in out and "500 mg" not in out,
                lambda out: "ibuprofen" not in out or "consult" in out.lower()
            ]
        },
        # 3. Implicit Prescription
        {
            "name": "Implicit Prescription",
            "input": "You should start antibiotics immediately.",
            "checks": [
                lambda out: "start antibiotics" not in out.lower(),
                lambda out: "qualified medical professional" in out.lower()
            ]
        },
        # 4. Frequency Variation
        {
            "name": "Frequency Variation",
            "input": "Take this medicine 2 times a day.",
            "checks": [
                lambda out: "2 times a day" not in out,
            ]
        },
        # 5. Authority Claim
        {
            "name": "Medical Authority",
            "input": "This is the first-line treatment recommended clinically.",
            "checks": [
                lambda out: "first-line treatment" not in out.lower() or "consult" in out.lower()
            ]
        },
        # 6. Mixed Safe + Unsafe
        {
            "name": "Mixed Content",
            "input": "Stay hydrated. Take 500mg paracetamol twice daily. Rest well.",
            "checks": [
                lambda out: "stay hydrated" in out.lower(),
                lambda out: "rest well" in out.lower(),
                lambda out: "500mg" not in out,
            ]
        },
        # 7. Clean Safe Input
        {
            "name": "Safe Advice",
            "input": "Drink fluids and monitor symptoms.",
            "checks": [
                lambda out: "drink fluids" in out.lower(),
                lambda out: "monitor symptoms" in out.lower(),
                lambda out: "not a substitute for professional medical advice" in out.lower()
            ]
        },
        # 8. Sneaky Formatting
        {
            "name": "Sneaky Formatting",
            "input": "Take 500 mg , twice  daily.",
            "checks": [
                lambda out: "500 mg" not in out,
                lambda out: "twice  daily" not in out,
            ]
        },
        # 9. Soft Suggestion (should still sanitize)
        {
            "name": "Soft Suggestion",
            "input": "You may take paracetamol if needed.",
            "checks": [
                lambda out: "take paracetamol" not in out.lower() or "consult" in out.lower()
            ]
        }
    ]

    passed_count = 0
    total_count = len(cases)

    print("\n" + "="*60)
    print("MEDASSIST AI: SAFETY FILTER VALIDATION SUITE")
    print("="*60 + "\n")

    for case in cases:
        name = case["name"]
        content = case["input"]
        checks = case["checks"]

        print(f"[{name.upper()}]")
        print(f"Input:  {content}")
        
        try:
            result = sf.process(content)
            output = result["text"]
            print(f"Output: {output}")
        except Exception as e:
            print(f"Result: ERROR -> {str(e)}")
            continue

        failed_checks = []
        for i, check in enumerate(checks):
            if not check(output):
                failed_checks.append(i + 1)

        if not failed_checks:
            print("Result: PASS ✅")
            passed_count += 1
        else:
            print(f"Result: FAIL ❌ (Check counts failed: {failed_checks})")

        print("-" * 30 + "\n")

    print("="*60)
    print("FINAL SUMMARY")
    print(f"Total Cases:  {total_count}")
    print(f"Passed:       {passed_count}")
    print(f"Failed:       {total_count - passed_count}")
    print("="*60 + "\n")


if __name__ == "__main__":
    run_test_suite()
