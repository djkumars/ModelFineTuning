import json
import logging
import os
from typing import Literal

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Support Ticket Classifier API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ClassificationRequest(BaseModel):
    description: str = Field(min_length=10, max_length=10_000)
    mode: Literal["baseline", "customized", "compare"] = "compare"


class ClassificationResult(BaseModel):
    category: str
    priority: str
    assignment_group: str
    confidence: float | None = Field(default=None, ge=0, le=1)


class ClassificationResponse(BaseModel):
    mode: Literal["baseline", "customized", "compare"]
    baseline: ClassificationResult | None = None
    customized: ClassificationResult | None = None
    agreement: bool | None = None


SYSTEM_PROMPT = """Classify an IT service-desk ticket. Return only a JSON object with
these fields: category, priority, assignment_group, confidence.
Use concise labels. confidence must be a number from 0 to 1 and is an
uncalibrated model estimate, not a statistically validated probability.
Do not include markdown or any text outside the JSON object."""


def _required_setting(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise HTTPException(
            status_code=503,
            detail=f"{name} is not configured. See the backend .env.example.",
        )
    return value


async def classify_with_model(description: str, variant: Literal["baseline", "customized"]) -> ClassificationResult:
    base_url = _required_setting("FOUNDRY_BASE_URL").rstrip("/")
    api_key = _required_setting("FOUNDRY_API_KEY")
    model = _required_setting(
        "FOUNDRY_BASELINE_MODEL" if variant == "baseline" else "FOUNDRY_CUSTOMIZED_MODEL"
    )
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": description},
        ],
        "temperature": 0,
    }

    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={"api-key": api_key},
                json=request_body,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            result = json.loads(content)
            return ClassificationResult.model_validate(result)
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Foundry request failed for %s with HTTP %s",
            variant,
            exc.response.status_code,
        )
        raise HTTPException(
            status_code=502,
            detail=f"The Azure AI Foundry {variant} model request failed with HTTP {exc.response.status_code}.",
        ) from exc
    except (httpx.RequestError, KeyError, IndexError, TypeError, json.JSONDecodeError, ValueError) as exc:
        logger.exception("Could not complete Foundry classification for %s", variant)
        raise HTTPException(
            status_code=502,
            detail=f"The Azure AI Foundry {variant} model returned an invalid response.",
        ) from exc


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/tickets/classify", response_model=ClassificationResponse)
async def classify_ticket(request: ClassificationRequest) -> ClassificationResponse:
    baseline = None
    customized = None

    if request.mode in ("baseline", "compare"):
        baseline = await classify_with_model(request.description, "baseline")
    if request.mode in ("customized", "compare"):
        customized = await classify_with_model(request.description, "customized")

    agreement = None
    if baseline is not None and customized is not None:
        agreement = (
            baseline.category.casefold() == customized.category.casefold()
            and baseline.priority.casefold() == customized.priority.casefold()
            and baseline.assignment_group.casefold()
            == customized.assignment_group.casefold()
        )

    return ClassificationResponse(
        mode=request.mode,
        baseline=baseline,
        customized=customized,
        agreement=agreement,
    )
