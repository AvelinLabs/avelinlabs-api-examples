# Input Quality Evaluation Set

Run each payload against `POST /api/v1/job/analyze` or `POST /api/v1/job/classify`.

The files intentionally cover:

- `strong.json`: clear responsibilities, tools, and domain evidence.
- `title-only.json`: insufficient context beyond a potentially ambiguous title.
- `vague.json`: generic workplace language with weak occupational evidence.
- `ambiguous.json`: plausible evidence spanning several occupational families.
- `noisy.json`: planning notes rather than a job description.

Inspect `confidence`, `uncertainty.total`, `is_ambiguous`, `domain_is_ambiguous`, `weak_signal_detected`, `weak_signal_reason`, `decision.decision`, matching skills, and explanations.

Do not assert fixed confidence values. The useful contract is conservative routing and inspectable evidence, not forcing every input into a confident occupation.
