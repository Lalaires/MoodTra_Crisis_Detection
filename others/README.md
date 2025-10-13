## Mindpal Crisis Detection

### Overview
This project implements an automated crisis-detection pipeline for teen chat messages. It:
- Ingests recent child messages from a PostgreSQL database
- Uses Hugging Face models to classify mental-health signals and generate an explanatory note
- Computes a severity level and stores a crisis alert back into the database
- Exposes an AWS Lambda-compatible entrypoint for batch processing across all accounts

### Key Components
- `crisis_pipeline.CrisisDetector`
  - Diagnosis model: `ethandavey/mental-health-diagnosis-bert` (multi-class probabilities)
  - Analysis model: `Tianlin668/MentalBART` (reasoned note; optionally sampled)
  - Combines probability-weighted severity with condition-based scaling into levels: `low`, `medium`, `high`, `extremely_high`.
- `main.py`
  - Database helpers: connection and query utilities using `psycopg2`
  - Data accessors: fetch latest child messages, last processed timestamp, account IDs
  - Processing: `process_crisis_detection(account_id)` and `process_all_accounts(connection)`
  - Persistence: writes to `crisis_alert` table with severity and optional note
  - `lambda_handler(event, context)`: entrypoint for AWS Lambda

### Expected Database Schema (minimal)
- `account(account_id)`
- `chat_session(session_id, account_id)`
- `chat_message(session_id, message_role, message_text, message_ts)`
- `crisis(crisis_id, crisis_name)`
- `crisis_alert(crisis_alert_id, account_id, crisis_id, crisis_alert_severity, crisis_alert_status, crisis_alert_note, crisis_alert_ts, last_msg_ts)`

### Environment Variables
Set the following for database access:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

### Requirements
Python 3.10+ recommended.

Install core dependencies:
```bash
pip install transformers torch psycopg2-binary
```

If running on AWS Lambda, use a compatible build of `torch` (CPU) or rely on a container image with prebuilt dependencies.

### How It Works
1. For each account, the pipeline fetches the latest N (10) child messages ordered by timestamp.
2. `CrisisDetector` computes a full probability distribution over classes and a weighted severity score.
3. If the score is above threshold, it generates an explanation and scales severity by detected condition.
4. If newer than the last processed timestamp, it writes a new entry to `crisis_alert`.
5. `process_all_accounts` aggregates counters and returns a summary.

### Running Locally
1. Export environment variables for DB connectivity.
2. Ensure the database contains the tables above and that `crisis` includes rows for expected names (e.g., `anxiety`, `depression`, `suicidal`, `stress`, `normal`).
3. Execute the Lambda handler or per-account processing, for example in a Python REPL:
```python
from main import create_connection, process_all_accounts
conn = create_connection()
summary = process_all_accounts(conn)
print(summary)
conn.close()
```

To invoke the Lambda entrypoint locally:
```python
from main import lambda_handler
resp = lambda_handler(event={}, context=None)
print(resp)
```

### Deployment (AWS Lambda)
- Package code with dependencies (or use a container image) and configure the Lambda handler to `main.lambda_handler`.
- Provide environment variables in Lambda configuration and network access to the database (VPC/subnets/security groups as needed).

### Notes
- First-time model loading is lazy-initialized and may add cold-start latency.
- GPU is optional; CPU inference is supported but slower.
- Messages are sanitized and trimmed to a safe length before analysis.

# Mindpal_Crisis_Detection