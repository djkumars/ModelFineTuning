# Support Ticket Classifier

A small Angular + TypeScript web UI and Python + FastAPI API for classifying IT service-desk tickets with Azure AI Foundry models. It is a classifier—not a chatbot—and includes a baseline-versus-customized comparison mode.

## What is included

- `frontend/`: Angular ticket-entry and model-comparison UI.
- `backend/`: FastAPI endpoint that calls OpenAI-compatible Azure AI Foundry deployments.
- `data/train.jsonl` and `data/validation.jsonl`: small synthetic JSONL examples for learning. Expand and review these before training; they are not production-quality data.
- `backend/scripts/upload_dataset.py`: optional upload of both JSONL files to an Azure Blob Storage container.

The starter does not provision Azure resources, train a model, or include credentials. Model calls return an explicit configuration error until Foundry endpoint/key/deployment settings are supplied.

## Run locally

1. Configure the API:

   ```powershell
   cd backend
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   Copy-Item .env.example .env
   ```

2. Set `FOUNDRY_BASE_URL`, `FOUNDRY_API_KEY`, `FOUNDRY_BASELINE_MODEL`, and `FOUNDRY_CUSTOMIZED_MODEL` in `backend/.env`, then load those values into the shell or your local environment manager. The URL should be the OpenAI-compatible inference URL ending in `/openai/v1`. Never commit `.env` or keys.

3. Start the API from `backend/`:

   ```powershell
   uvicorn app.main:app --reload --env-file .env
   ```

4. In another terminal, start the UI:

   ```powershell
   cd frontend
   npm install
   npm start
   ```

   Open `http://localhost:4200`. The development proxy forwards `/api` requests to `http://127.0.0.1:8000`.

## API

`POST /api/tickets/classify`

```json
{
  "description": "I am locked out of my account and cannot sign in.",
  "mode": "compare"
}
```

`mode` can be `baseline`, `customized`, or `compare`. The result includes a category, priority, assignment group, optional model-reported confidence, and (in comparison mode) whether the models agree. Model-reported confidence is uncalibrated and should not be used as a decision threshold.

## Dataset upload

After creating and configuring an Azure Storage account, set `AZURE_STORAGE_CONNECTION_STRING` and optionally `AZURE_STORAGE_CONTAINER`, then run from the project root:

```powershell
py -m pip install -r backend/requirements.txt
py backend/scripts/upload_dataset.py
```

Review current Azure AI Foundry fine-tuning model/region availability and the required JSONL format in your Foundry project before submitting a training job. The included examples are only a format demonstration.

## Security scope

The API is unauthenticated and configured for local development. Do not expose it publicly without adding authentication, authorization, rate limiting, and production-grade secret management.
