from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import boto3
from botocore.config import Config

from app.core.config import Settings, get_settings


class LlmService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def complete(self, prompt: str) -> str:
        return await asyncio.to_thread(self._complete_sync, prompt)

    async def complete_json(self, prompt: str) -> dict[str, Any]:
        text = await self.complete(prompt)
        return self._parse_json(text)

    def _complete_sync(self, prompt: str) -> str:
        if not self.settings.aws_access_key_id or not self.settings.aws_secret_access_key:
            raise RuntimeError("AWS Bedrock credentials are not configured for Sherlock analysis planning.")

        client = boto3.client(
            "bedrock-runtime",
            region_name=self.settings.aws_default_region or "us-east-1",
            aws_access_key_id=self.settings.aws_access_key_id,
            aws_secret_access_key=self.settings.aws_secret_access_key,
            config=Config(
                connect_timeout=5,
                read_timeout=30,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        )
        model_id = self.settings.bedrock_model_id
        body = self._request_body(model_id, prompt)
        response = client.invoke_model(modelId=model_id, body=json.dumps(body), contentType="application/json")
        payload = json.loads(response["body"].read())
        return self._response_text(model_id, payload)

    def _request_body(self, model_id: str, prompt: str) -> dict[str, Any]:
        if model_id.startswith("meta."):
            return {
                "prompt": self._format_llama_prompt(prompt),
                "max_gen_len": self.settings.bedrock_max_tokens,
                "temperature": self.settings.bedrock_temperature,
                "top_p": 0.9,
            }
        if model_id.startswith("anthropic."):
            return {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.settings.bedrock_max_tokens,
                "temperature": self.settings.bedrock_temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
        return {
            "inputText": prompt,
            "textGenerationConfig": {
                "maxTokenCount": self.settings.bedrock_max_tokens,
                "temperature": self.settings.bedrock_temperature,
                "topP": 0.9,
            },
        }

    def _response_text(self, model_id: str, payload: dict[str, Any]) -> str:
        if model_id.startswith("meta."):
            return str(payload.get("generation") or payload.get("outputs", [{}])[0].get("text") or "")
        if model_id.startswith("anthropic."):
            content = payload.get("content") or []
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if "results" in payload:
            return str(payload["results"][0].get("outputText", ""))
        return str(payload.get("outputText") or payload.get("generation") or payload)

    def _format_llama_prompt(self, prompt: str) -> str:
        return (
            "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n"
            f"{prompt}"
            "<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        )

    def _parse_json(self, text: str) -> dict[str, Any]:
        stripped = text.strip()
        if stripped.startswith("```"):
            stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
            stripped = re.sub(r"```$", "", stripped).strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
            if not match:
                raise
            parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise ValueError("LLM response must be a JSON object.")
        return parsed
