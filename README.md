## MoodTra Crisis Detection Pipeline

A end-to-end pipeline that detects mental-health crisis signals from recent chat messages and raises database alerts. It combines a Hugging Face classifier for diagnosis probabilities with a Google GenAI model to assign a severity level.

### How it works

- Collects the latest child messages per account from the database.
- Computes a diagnosis distribution with `ethandavey/mental-health-diagnosis-bert`.
- Prompts a Gemini model to determine severity using clear, auditable rules.
- Stores an alert in `crisis_alert` linked to the matched `crisis` entry.

### Output (from the severity agent)

```json
{
  "crisis_name": "<Anxiety|Normal|Depression|Suicidal|Stress>",
  "crisis_note": "<one-sentence rationale>",
  "severity": "<low|medium|high|extremely high>"
}
```

### Environment variables

- `GOOGLE_API_KEY`: Google GenAI API key (required)
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`: Postgres connection (required)
- `HF_HOME`: Optional cache dir for model weights (defaults to system cache)

### Docker / AWS Lambda

This repo ships a Lambda base image (`public.ecr.aws/lambda/python:3.13`).

Build:

```bash
docker build -t crisis-pipeline .
```

### Files

- `crisis_pipeline.py`: HF model inference + Gemini severity agent.
- `main.py`: DB I/O, batching, and Lambda handler `main.lambda_handler`.
- `Dockerfile`: Lambda-compatible container.
- `test_agent.ipynb`: Ad-hoc testing and exploration.

### Requirements

See `requirements.txt`. Internet access is required to download model weights and call Google GenAI.

### License

MIT (see `LICENSE`).
