# EchoGrid Limitations

EchoGrid is a synthetic simulation tool. It is designed for education, research discussion, demo storytelling, and communication-risk exploration.

## Not Prediction

EchoGrid does not measure real public opinion. Synthetic agents are plausible personas, not survey respondents. Outputs must not be cited as polling, forecasting, or evidence about actual groups.

## Not Calibration

The current population generator is deterministic and coherent enough for demos, but it is not calibrated to external demographic, media, or behavioral datasets. Calibration hooks are future research infrastructure, and even calibrated runs would need careful uncertainty language.

## Model Bias And Prompt Sensitivity

Hybrid and Full LLM sample modes depend on provider behavior, prompt wording, schema validation, and fallback handling. Different models may produce different framings, comments, or reaction styles.

## Diffusion Model

Echo cascades are bubble-based. Media actors target social bubbles, and agents receive one echo item per round. This is useful for explainable demos, but it is not graph-based social-network diffusion.

## Safety Boundary

EchoGrid must not be used to optimize manipulative persuasion, political targeting, harassment, radicalization, or targeting vulnerable groups. The app, exports, and docs repeat this limitation because synthetic segments can still be misused if treated as targetable audiences.

## Storage

SQLite persistence stores flexible JSON payloads for local MVP use. It is not a migration-managed analytical warehouse and should not be treated as a multi-user production database.
