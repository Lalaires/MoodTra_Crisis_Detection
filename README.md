### Mindpal Crisis Detection – Architecture and Deployment Guide

This document explains the end-to-end flow of the crisis detection pipeline, how it is packaged into a container and deployed to AWS Lambda, and how it is scheduled via AWS EventBridge.

## Overview

- **Purpose**: Analyze recent child chat messages to detect potential crisis signals and store alerts in a PostgreSQL database.
- **Key components**:
  - `crisis_pipeline.py`: Model loading and crisis inference (diagnosis, analysis, scoring, severity).
  - `main.py`: Database I/O, batching logic across accounts, and the AWS Lambda handler.
  - `Dockerfile`: Builds a Lambda-compatible container image.
  - `requirements.txt`: Python dependencies.

## Data Flow

1. Lambda starts and initializes a singleton `CrisisDetector` (lazy initialization avoids reloading models per invocation).
2. Lambda connects to PostgreSQL (RDS) using env vars.
3. For each account:
   - Fetch latest 10 child messages and build a newline-joined context.
   - Run crisis detection and compute severity.
   - Upsert a corresponding alert record with timestamp gating to avoid duplicates.
4. Return a compact summary and log to CloudWatch.

### Core Logic – `crisis_pipeline.py`

- Uses Hugging Face models:
  - `Tianlin668/MentalBART` for analysis/condition extraction.
  - `ethandavey/mental-health-diagnosis-bert` for multi-class diagnosis probabilities.
- Computes a diagnosis-weighted score, then scales by detected condition; maps to severity levels: `low`, `medium`, `high`, `extremely_high`.
- Thresholding is applied so full analysis only triggers above a base score.

Code reference (inference entrypoint):
```126:141:/home/cyra/code/Mindpal_Crisis_Detection/crisis_pipeline.py
    def detect_crisis(self, text: str) -> Dict[str, str]:
        # Get full probability distribution
        all_probs, top_prediction = self.crisis_diagnosis(text)

        score = self.severity_score(all_probs)
        if score >= 0.39:
            # Get detailed analysis
            condition, completion = self.crisis_analysis(text)
            severity = self.severity_scaling(score, condition)
            if severity != "low":
                return {
                    "crisis_name": top_prediction,
                    "crisis_note": completion,
                    "severity": severity,
                }
            else:
                return {
                    "crisis_name": top_prediction,
                    "crisis_note": None, 
                    "severity": severity
                }
        else:
            return {
                "crisis_name": top_prediction,
                "crisis_note": None, 
                "severity": "low"
            }
```

### Orchestration – `main.py`

- Connection management: pulls `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT` from env vars and creates a psycopg2 connection.
- Batch processing:
  - Retrieves all `account_id` values, iterates, and processes 10 most recent child messages per account.
  - Uses `MAX(last_msg_ts)` gating to skip already-processed batches.
  - Writes to `crisis_alert` with severity, optional note, and `last_msg_ts`.
- Lambda handler returns a compact JSON summary; logs details to CloudWatch.

Code reference (Lambda entrypoint):
```346:375:/home/cyra/code/Mindpal_Crisis_Detection/main.py
def lambda_handler(event, context):
    """
    Main Lambda handler function - Crisis Detection Pipeline for All Accounts
    """
    connection = None
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        logger.info("Starting Crisis Detection Lambda function for all accounts...")
        connection = create_connection()
        result = process_all_accounts(connection)
        logger.info(f"Crisis detection completed for all accounts: {result}")
        return { 'statusCode': 200, 'headers': { 'Content-Type': 'application/json' }, 'body': json.dumps({ 'success': True, 'message': 'Crisis detection completed for all accounts', 'result': result }) }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return { 'statusCode': 500, 'headers': { 'Content-Type': 'application/json' }, 'body': json.dumps({ 'success': False, 'error': str(e) }) }
    finally:
        if connection:
            connection.close()
            logger.info("Database connection closed")
```

## Environment and Configuration

Set these env vars in Lambda (or your container runtime):

- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`: PostgreSQL connection
- `HF_HOME` (defaulted in `Dockerfile` to `/tmp/hf`): cache location for HF models

Database tables expected by queries:

- `account(account_id)`
- `chat_session(session_id, account_id)`
- `chat_message(session_id, message_text, message_ts, message_role)`
- `crisis(crisis_id, crisis_name)`
- `crisis_alert(crisis_alert_id, account_id, crisis_id, crisis_alert_severity, crisis_alert_status, crisis_alert_note, crisis_alert_ts, last_msg_ts)`

## Containerization (AWS Lambda base image)

`Dockerfile` summary:

```1:21:/home/cyra/code/Mindpal_Crisis_Detection/Dockerfile
FROM public.ecr.aws/lambda/python:3.13
COPY requirements.txt  ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py ${LAMBDA_TASK_ROOT}
COPY crisis_pipeline.py ${LAMBDA_TASK_ROOT}
ENV DB_HOST=url_to_db
ENV DB_NAME=name_of_db
ENV DB_USER=user_of_db
ENV DB_PASSWORD=password_of_db
ENV DB_PORT=port_of_db
ENV HF_HOME=/tmp/hf
CMD [ "main.lambda_handler" ]
```

Notes:

- The image uses Python 3.13 Lambda runtime.
- CPU-only `torch` wheel is installed; ensure architecture compatibility with your Lambda (x86_64 recommended for this image).
- HF cache uses `/tmp`; adjust Lambda ephemeral storage to accommodate model sizes.

### Build and Push to ECR

Replace placeholders with your values (`$AWS_ACCOUNT_ID`, `$AWS_REGION`, `$REPO`, `$TAG`).

```bash
aws ecr create-repository --repository-name $REPO --image-scanning-configuration scanOnPush=true --region $AWS_REGION
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

docker build -t $REPO:$TAG .
docker tag $REPO:$TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO:$TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO:$TAG
```

## Deploy to AWS Lambda (Container Image)

1. Create function from container image and select the ECR image.
2. Set handler to `main.lambda_handler` (already specified by `CMD`).
3. Configure environment variables (`DB_*`, `HF_HOME`).
4. VPC configuration:
   - Attach the Lambda to the RDS VPC and subnets.
   - Security group must allow outbound to the RDS instance; RDS SG must allow inbound from Lambda SG on `DB_PORT`.
   - Attach the managed policy `AWSLambdaVPCAccessExecutionRole` to the Lambda’s execution role.
5. Set resource limits appropriately:
   - Memory: 4096–8192 MB (model inference is CPU-bound and benefits from more memory/CPU).
   - Timeout: 300–600 seconds depending on account volume.
   - Ephemeral storage (`/tmp`): 1024–4096 MB+ to cache HF models.
6. IAM permissions: execution role needs `logs:*` for CloudWatch; ECR read is handled by the service when you select the image.

### Test Invocation

```bash
aws lambda invoke \
  --function-name <your-fn-name> \
  --payload '{}' \
  --cli-binary-format raw-in-base64-out \
  out.json && cat out.json
```

Check CloudWatch Logs for initialization and processing summaries.

## Scheduling with EventBridge

Create a rule to run the function on a cadence (example: every 15 minutes):

```bash
aws events put-rule \
  --name crisis-detection-quarter-hour \
  --schedule-expression 'rate(15 minutes)'

aws lambda add-permission \
  --function-name <your-fn-name> \
  --statement-id eb-invoke \
  --action 'lambda:InvokeFunction' \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:$AWS_REGION:$AWS_ACCOUNT_ID:rule/crisis-detection-quarter-hour

aws events put-targets \
  --rule crisis-detection-quarter-hour \
  --targets "Id"="1","Arn"="arn:aws:lambda:$AWS_REGION:$AWS_ACCOUNT_ID:function:<your-fn-name>","Input"='{}'
```

Alternatively, configure the rule and target via the AWS Console. Keep input `{}` unless you add optional parameters.

## Operational Notes

- Cold starts: first invocation will download/load HF models; subsequent invocations reuse the singleton.
- Concurrency: if running at scale, ensure the RDS can handle concurrent connections; consider connection pooling (e.g., RDS Proxy).
- Idempotency: timestamp gating (`MAX(last_msg_ts)`) prevents duplicate alert creation across invocations.
- Observability: use CloudWatch metrics and logs; consider structured logging and alerts on errors.
- Cost: batch per account to reduce invocations; tune schedule cadence as needed.



