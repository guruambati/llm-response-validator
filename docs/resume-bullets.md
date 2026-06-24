# Resume Bullets — LLM Response Validator

Use these in the Projects section of your resume. Choose the version that best fits
the role description.

---

## Option A — AI QA / LLM Evaluation focus

- Built a pytest-based LLM response validation framework with 40+ tests covering
  structural, semantic, safety, and performance checks; catches PII leakage, JSON
  schema violations, harmful content patterns, and latency SLA breaches in LLM outputs

---

## Option B — AI SDET / Test Automation focus

- Designed and implemented a fluent validation API for LLM responses (Python, pytest)
  that enforces quality contracts including keyword coverage, output format, token
  budget, and safety rules; integrated with GitHub Actions CI to gate every push

---

## Option C — GenAI QA Engineer focus

- Developed a reusable quality assurance library for GenAI outputs with chainable
  checks (not_empty, valid_json, no_pii, latency_under_ms) and JSON report generation;
  built to demonstrate systematic AI quality engineering practices independent of any
  specific LLM vendor

---

## Notes on Usage

- Do not claim "production" or "enterprise" use — present as a portfolio/learning project
- Pair with a brief verbal explanation: "I built this to understand how to bring
  traditional QA discipline — contracts, assertions, CI gates — to LLM outputs"
- Strong talking point: "The design is vendor-agnostic — it works with any LLM because
  it validates the response, not the model itself"
