# MoodTra Crisis Detection Pipeline

An automated mental health crisis detection system that analyzes chat messages from teenagers and generates severity-based alerts. This pipeline combines machine learning models with rule-based severity assessment to identify and escalate mental health concerns.

## 🎯 Overview

This system processes chat messages from 13-15 year-old users to detect mental health crisis signals. It uses a two-stage approach:
1. **ML-based diagnosis** using a fine-tuned BERT model to classify mental health states
2. **LLM-based severity assessment** using Google Gemini to assign crisis severity levels according to a set of rules

Results are stored in a PostgreSQL database for monitoring and intervention by caregivers or support teams.

## 🔗 Links for MoodTra
- Website: [MoodTra](https://moodtra.tech/)
- GitHub Repositories:
    - [MoodTra_Frontend](https://github.com/yihui1306/mindPal-frontend)
    - [MoodTra_Backend](https://github.com/Lalaires/MindPal_Backend)
    - MoodTra_Crisis_Detection - Current Repo

## ✨ Features

- **Batch Processing**: Analyzes the latest 10 messages per user as context
- **Multi-class Detection**: Identifies Anxiety, Depression, Stress, Suicidal ideation, or Normal states
- **Severity Rating**: Classifies crisis levels as Low, Medium, High, or Extremely High
- **Duplicate Prevention**: Tracks processed messages to avoid redundant alerts, skip the crisis detection if the account's latest message has already been processed
- **AWS Lambda Ready**: Containerized for serverless deployment
- **Scalable**: Processes all child accounts in a single invocation

## 🚀 Deployment Status

**Currently deployed on AWS** using the following infrastructure:
- **AWS Lambda**: Serverless execution of crisis detection pipeline
- **Amazon RDS**: PostgreSQL database for message storage and alert management
- **Amazon ECR**: Container registry hosting the Docker image
- **Amazon EventBridge**: Scheduled triggers for automated batch processing

## 🏗️ Architecture

### Pipeline Flow

```
Chat Messages (PostgreSQL)
    ↓
Fetch Latest 10 Messages per Account
    ↓
Mental Health Diagnosis (Mental Health Diagnosis BERT Model)
    ↓
Severity Assessment (Google Gemini)
    ↓
Store Alert (PostgreSQL crisis_alert table)
```

### Components

**`crisis_pipeline.py`**
- `CrisisDetector`: Main detection class
  - `crisis_diagnosis()`: BERT-based mental health classification
  - `severity_rating_agent()`: Gemini-powered severity assessment with detailed prompts
  - `detect_crisis()`: End-to-end detection pipeline

**`main.py`**
- Database connection and query management
- Message fetching and deduplication logic
- Crisis alert storage
- AWS Lambda handler for batch processing all accounts

## 📋 Requirements

- Python 3.13
- PostgreSQL database with schema containing:
  - `account` table (child accounts)
  - `chat_message` table (user messages)
  - `chat_session` table (session metadata)
  - `crisis` table (crisis types)
  - `crisis_alert` table (generated alerts)

### Python Dependencies

```
transformers
torch (CPU version)
psycopg2-binary
google-genai
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google GenAI API key for Gemini model | ✅ |
| `DB_HOST` | PostgreSQL host URL | ✅ |
| `DB_NAME` | Database name | ✅ |
| `DB_USER` | Database username | ✅ |
| `DB_PASSWORD` | Database password | ✅ |
| `DB_PORT` | Database port (default: 5432) | ✅ |
| `HF_HOME` | Hugging Face cache directory (default: /tmp/hf) | ⬜ |

### Severity Level Definitions

| Level | Description | Examples |
|-------|-------------|----------|
| **Low** | Mild or situational distress, no suicidal thoughts | "Tired from homework", "Feeling better" |
| **Medium** | Noticeable emotional distress, functional impact, no self-harm | "Can't focus anymore", "Everything feels pointless" |
| **High** | Strong distress, hopelessness, suicidal ideation without plan, or self-harm | "I wish I could disappear", "I cut to feel something" |
| **Extremely High** | Imminent suicide risk with plan, intent, means, or timeframe | "I'm ending it tonight", "I have the pills ready" |

## 🗂️ Project Structure

```
MoodTra_Crisis_Detection/
├── crisis_pipeline.py      # ML models and severity assessment logic
├── main.py                 # Database operations and Lambda handler
├── requirements.txt        # Python dependencies
├── Dockerfile              # AWS Lambda container configuration
├── test_agent.ipynb        # Testing and experimentation notebook
├── LICENSE                 # MIT License
└── README.md               # This file
```

## 🧪 Testing

Use the included Jupyter notebook for local testing:

This allows you to:
- Test individual message detection
- Experiment with severity prompts
- Validate model outputs
- Debug edge cases

## 📊 Monitoring

Key metrics to track:
- Total accounts processed per invocation
- Number of alerts created by severity level
- Failed account processing count
- Lambda execution time and memory usage
- Model inference latency

## 🤝 Support & Contact

For issues, questions, or collaboration requests:
- Contact the development team - 📧 Email: claireaus066@gmail.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**⚠️ Important Note:** This system is designed to assist in crisis detection but should not replace professional mental health assessment. Always ensure proper escalation procedures and human oversight are in place for high and extremely high severity alerts.
