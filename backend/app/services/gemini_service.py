import time
import httpx
from datetime import datetime, timezone
from typing import Optional
from google import genai
from google.genai import types

from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)


class GeminiSDK:
    def __init__(self):
        self.model_name = "gemini-2.5-flash"
        self.provider = "google"

    def _build_history(self, messages: list[dict]) -> list[types.Content]:
        history = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            history.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])]
                )
            )
        return history

    def chat(
        self,
        message: str,
        history: list[dict],
        conversation_id: Optional[str] = None,
    ) -> dict:
        started_at = datetime.now(timezone.utc)
        start_time = time.perf_counter()

        try:
            gemini_history = self._build_history(history)

            response = client.models.generate_content(
                model=self.model_name,
                contents=gemini_history + [
                    types.Content(
                        role="user",
                        parts=[types.Part(text=message)]
                    )
                ],
            )

            end_time = time.perf_counter()
            ended_at = datetime.now(timezone.utc)
            latency_ms = round((end_time - start_time) * 1000, 2)

            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count if usage else None
            output_tokens = usage.candidates_token_count if usage else None
            total_tokens = usage.total_token_count if usage else None
            response_text = response.text

            self._ship_log(
                conversation_id=conversation_id,
                started_at=started_at,
                ended_at=ended_at,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                status="success",
                input_preview=message,
                output_preview=response_text,
            )

            return {
                "text": response_text,
                "latency_ms": latency_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            }

        except Exception as e:
            end_time = time.perf_counter()
            ended_at = datetime.now(timezone.utc)
            latency_ms = round((end_time - start_time) * 1000, 2)
            self._ship_log(
                conversation_id=conversation_id,
                started_at=started_at,
                ended_at=ended_at,
                latency_ms=latency_ms,
                status="error",
                error_message=str(e),
            )
            raise

    def _ship_log(self, **kwargs):
        try:
            payload = {
                "model": self.model_name,
                "provider": self.provider,
                "started_at": kwargs["started_at"].isoformat(),
                "ended_at": kwargs["ended_at"].isoformat(),
                "latency_ms": kwargs["latency_ms"],
                "status": kwargs.get("status", "success"),
                "conversation_id": kwargs.get("conversation_id"),
                "input_tokens": kwargs.get("input_tokens"),
                "output_tokens": kwargs.get("output_tokens"),
                "total_tokens": kwargs.get("total_tokens"),
                "error_message": kwargs.get("error_message"),
                "input_preview": kwargs.get("input_preview", "")[:200],
                "output_preview": kwargs.get("output_preview", "")[:200],
            }
            with httpx.Client(timeout=3.0) as client:
                client.post(
                    "http://127.0.0.1:8000/api/v1/logs/ingest",
                    json=payload,
                )
        except Exception:
            pass


gemini_sdk = GeminiSDK()