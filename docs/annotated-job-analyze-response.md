# Annotated Job Analyze Response

This guide explains `responses/job-analyze.example.json` in plain English.

The example is illustrative for the current beta. Treat fields as decision-support signals, not final truth or guaranteed production behavior. Clients should ignore unknown additive fields and avoid depending on debug-only fields.

| Field | Plain-English meaning | Why it matters |
| ----- | --------------------- | -------------- |
| `confidence` | Overall confidence signal for the top analysis result. | Helps decide whether the output is strong enough to show, use, or route for review. It is not an absolute probability. |
| `trust_score` | Trust-oriented score that combines result strength with quality support. | Gives another signal for how much support exists behind the selected result. |
| `uncertainty.total` | Combined uncertainty signal for the analysis. | Higher uncertainty means the input or evidence may need human review. |
| `decision.decision` | Routing label such as `AUTO_ACCEPT`, `REVIEW`, `REJECT`, or `AMBIGUOUS`. | Helps products decide the next workflow step without inventing routing logic from raw scores alone. |
| `decision.reason` | Human-readable reason for the routing label. | Helps reviewers understand why the result was accepted, reviewed, rejected, or marked ambiguous. |
| `job_signals` | Skill, tool, task, or domain signals detected from the input text. | Shows which parts of the job text influenced the analysis. |
| `results[].onet_code` | O*NET occupation code for a ranked candidate. | Provides a standardized occupation identifier for downstream systems. |
| `results[].title` | Occupation title for the ranked candidate. | Gives a readable label for the matched occupation. |
| `results[].confidence` | Confidence for that candidate within the ranked result set. | Helps compare the top match against other candidate occupations. |
| `results[].matching_skills` | Skills or capabilities that support the match. | Gives consultants, reviewers, or product workflows evidence for why the occupation was selected. |
| `results[].quality_score` | Aggregate quality signal for the candidate result. | Helps assess whether the match has enough supporting evidence to be useful. |
| `results[].domain_grounding` | Categorical support level for the candidate within the supported domain. | Helps identify whether the result is strongly grounded or should be treated cautiously. |
| `results[].explanation.why_match` | Plain-English explanation of why the candidate occupation matches the input. | Makes the output easier for reviewers and client-facing teams to interpret. |

## Practical Review Guidance

Use high-confidence, low-uncertainty results as candidates for low-risk automation or direct display where your product policy allows it.

Route outputs to review when confidence is lower, uncertainty is higher, the decision label is `REVIEW` or `AMBIGUOUS`, or the job text describes a role that overlaps multiple departments or occupation families.

Do not treat the example response as a complete API contract. Use the public API documentation and your live beta response payloads as the integration reference.
