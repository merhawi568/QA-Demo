from typing import Dict, Any, Optional
import json

LLM_EXTRACTION_PROMPT = """You are a precise information extractor.
You will receive raw text from a PDF. Extract ONLY the fields requested in the JSON schema keys.
Respond with a valid, minified JSON object using EXACTLY these keys (no extra keys, no commentary).
Keys: {keys}

Text:
{body}

Rules:
- If a field is missing, set it to null.
- For dates, prefer ISO format YYYY-MM-DD if present; otherwise leave as-is.
- Output JSON only.
"""

def extract_json_with_llm(llm, text: str, expected_keys: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        prompt = LLM_EXTRACTION_PROMPT.format(
            keys=list(expected_keys.keys()),
            body=text[:15000]
        )
        out = llm.invoke(prompt)
        raw = out.content if hasattr(out, "content") else str(out)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json", "", 1).strip()
        return json.loads(raw)
    except Exception:
        return None
