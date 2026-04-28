# EchoGrid Ethics And Safety Notes

EchoGrid generates synthetic reactions. It is not a polling tool, a public-opinion predictor, or evidence of actual population beliefs.

## Allowed Uses

- Research and education about media dynamics.
- Communication-risk analysis that reduces confusion or harm.
- Scenario exploration for synthetic public-message reactions.
- Demonstrations of echo effects, distortion, trust shifts, and polarization dynamics.

## Disallowed Uses

EchoGrid must not be used to optimize manipulative persuasion, political targeting, harassment, radicalization, or targeting vulnerable groups. The app and exports include this warning because synthetic personas can still be misused as if they were real audience segments.

## Design Guardrails

- Mock mode is deterministic and explicitly synthetic.
- Exports include disclaimers in CSV metadata comments and summary JSON.
- `src.guardrails.classify_request` blocks common manipulative targeting requests.
- Provider scaffolding exists, but full-scale LLM agent simulation is not enabled in the release build.

## Developer Guidance

When adding LLM mode, keep explicit cost limits, sample-size limits, and refusal behavior in the user flow. Do not add workflows that rank demographic groups by persuadability or produce optimized targeting copy. Analytics should describe synthetic risk patterns, not prescribe manipulation.
