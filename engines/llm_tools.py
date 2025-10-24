# engines/llm_tools.py
from typing import Dict, Any, Optional
import json

LLM_EXTRACTION_PROMPT = """You are a precise information extractor.
You will receive raw text from a PDF. Extract ONLY the fields requested in the JSON schema keys.
Respond with a valid, minified JSON object using EXACTLY these keys:
{keys}

Text:
{body}
Rules:
- If a field is missing, set it to null.
- For dates, prefer ISO format YYYY-MM-DD if present; otherwise leave as-is.
- Do not add extra keys or commentary. Output JSON only.
"""

def extract_json_with_llm(llm, text: str, expected_keys: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Use OpenAI (LangChain chat model) to coerce free text into a specific JSON schema."""
    try:
        prompt = LLM_EXTRACTION_PROMPT.format(
            keys=list(expected_keys.keys()),
            body=text[:15000]  # safety truncation for demo
        )
        out = llm.invoke(prompt)
        raw = out.content if hasattr(out, "content") else str(out)
        # best-effort to strip code fences
        raw = raw.strip().strip("```").replace("json", "", 1).strip()
        return json.loads(raw)
    except Exception:
        return None
