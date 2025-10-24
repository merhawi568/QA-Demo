# engines/llm_tools.py
from typing import Dict, Any, Optional
import json

LLM_EXTRACTION_PROMPT = """You are a precise information extractor.
You will receive raw text from a PDF. Extract ONLY the fields requested in the JSON schema keys.
Respond with a valid, minified JSON object using EXACTLY these keys:
{keys}

Text:
