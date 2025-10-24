from typing import Dict, Any, Optional
import re
from dateutil import parser as dateparser
import pdfplumber

def _normalize_name(s: Optional[str]) -> Optional[str]:
    if not s: return s
    return re.sub(r"[^A-Za-z ]", "", s).upper().strip()

def _normalize_date(s: Optional[str]) -> Optional[str]:
    if not s: return s
    try:
        dt = dateparser.parse(s, dayfirst=False, yearfirst=False, fuzzy=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return s

class DocumentExtractionAgent:
    """
    Extracts key fields from a PDF using Python first (regex/heuristics),
    then (optionally) refines with an LLM to produce a JSON object that matches a schema.
    """
    def __init__(self, llm=None):
        self.llm = llm

    def _extract_text(self, pdf_path: str) -> str:
        chunks = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                txt = page.extract_text() or ""
                chunks.append(txt)
        return "\n".join(chunks)

    def _python_first_pass(self, text: str, expected_schema: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {k: None for k in expected_schema.keys()}
        m_name = re.search(r"(Client|Customer)\s*Name\s*:\s*(.+)", text, re.IGNORECASE)
        if m_name:
            out["client_name"] = _normalize_name(m_name.group(2))
        m_dob = re.search(r"(DOB|Date of Birth)\s*:\s*([A-Za-z0-9 ,\-\/]+)", text, re.IGNORECASE)
        if m_dob:
            out["dob"] = _normalize_date(m_dob.group(2))
        m_eff = re.search(r"(Effective\s*Date)\s*:\s*([A-Za-z0-9 ,\-\/]+)", text, re.IGNORECASE)
        if m_eff:
            out["effective_date"] = _normalize_date(m_eff.group(2))
        return out

    def extract_fields(self, pdf_path: str, expected_schema: Dict[str, Any]) -> Dict[str, Any]:
        text = self._extract_text(pdf_path)
        draft = self._python_first_pass(text, expected_schema)

        if self.llm:
            from engines.llm_tools import extract_json_with_llm
            llm_json = extract_json_with_llm(self.llm, text, expected_schema)
            if llm_json:
                if "client_name" in llm_json:
                    llm_json["client_name"] = _normalize_name(llm_json.get("client_name"))
                if "dob" in llm_json:
                    llm_json["dob"] = _normalize_date(llm_json.get("dob"))
                if "effective_date" in llm_json:
                    llm_json["effective_date"] = _normalize_date(llm_json.get("effective_date"))
                for k in expected_schema.keys():
                    if llm_json.get(k):
                        draft[k] = llm_json[k]
        return draft
