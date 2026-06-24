# Interview Notes — LLM Response Validator

## What I Built

A pytest-based quality assurance framework that validates LLM API responses against
structural, semantic, safety, and performance contracts. The core design is a **fluent
validator** — you chain checks in one readable expression, similar to how assertions
work in RestAssured for API testing.

## How I Would Explain It in an Interview

> "When teams ship features powered by LLMs, the outputs aren't deterministic the way
> a traditional API response is. I built a validation framework to bring systematic
> quality gates to those outputs. It has four categories of checks:
>
> **Structural** — is it non-empty, within length limits, valid JSON, does it have the
> expected keys?
>
> **Semantic** — does it contain the required keywords, match expected patterns, avoid
> refusal signals?
>
> **Safety** — does it contain PII like email addresses or SSNs? Does it include
> harmful instruction patterns?
>
> **Performance** — is the latency within the SLA threshold, is token usage within budget?
>
> The API is fluent and chainable, so a test case reads almost like natural language.
> You can call `assert_all_pass()` and get a full failure report showing which specific
> checks failed and why. There's also a JSON reporter for CI integration."

## What QA Problem It Solves

Traditional assertion (`assert response == expected`) breaks down for LLM outputs
because responses are never identical. This framework solves:

1. **No clear contract** — establishes explicit quality contracts per endpoint
2. **Silent degradation** — catches regressions that only show up as response quality drift
3. **Safety blind spots** — automated PII and harmful content detection in outputs
4. **SLA visibility** — latency and token checks give ops teams observability signals
5. **CI integration** — every push validates LLM quality automatically

## Design Decisions Worth Discussing

**Why fluent/chainable API?**
Inspired by RestAssured (Java) and pytest-BDD. Makes test cases readable during
code review and easy to extend with one more `.check()` call.

**Why separate `checks.py` from `core.py`?**
Separation of concerns. Individual check functions are pure and stateless — you can
unit-test them directly without the validator wrapper. This also makes adding new
check types straightforward.

**Why no external NLP library for semantic checks?**
Kept it dependency-free so it runs anywhere without GPU/internet. The trade-off:
keyword matching is lexical, not semantic. The improvement path is to add an optional
`sentence-transformers` integration for embedding-based checks.

## What I Would Add Next

1. **Semantic similarity check** using `sentence-transformers` — compare against
   a golden answer using cosine similarity rather than exact keyword matching
2. **LLM-as-judge integration** — use a secondary LLM call to evaluate correctness
3. **Async support** — validate streaming responses as they arrive
4. **pytest plugin** — wrap the validator as a pytest fixture so teams can use it
   without importing anything
5. **Threshold configuration** — load thresholds from a YAML config file rather than
   hardcoding values in each test
