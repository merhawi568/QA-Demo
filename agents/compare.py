# agents/compare.py (add)
def name_equals(a, b):
    from re import sub
    def clean(x): 
        return sub(r"[^A-Za-z ]","", str(x)).upper().strip()
    ca, cb = clean(a), clean(b)
    ok = ca == cb
    return {"passed": ok, "reason": f"{ca} == {cb}" if ok else f"{ca} != {cb}", "left": a, "right": b}

from datetime import datetime, timedelta
from typing import Any, Dict

def _to_dt(v: Any) -> datetime:
    if isinstance(v, datetime):
        return v
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(v), fmt)
        except Exception:
            pass
    raise ValueError(f"Unrecognized datetime: {v}")

def equals(left: Any, right: Any, normalize: bool = False) -> Dict[str, Any]:
    l, r = str(left), str(right)
    if normalize:
        l = l.replace("-", "").replace(" ", "").upper()
        r = r.replace("-", "").replace(" ", "").upper()
    ok = l == r
    return {"passed": ok, "reason": f"{l} == {r}" if ok else f"{l} != {r}", "left": left, "right": right}

def rounded_equality(a: Any, b: Any, places: int = 2) -> Dict[str, Any]:
    ra, rb = round(float(a), places), round(float(b), places)
    ok = ra == rb
    return {"passed": ok, "reason": f"{ra} == {rb} @ {places}dp" if ok else f"{ra} != {rb} @ {places}dp", "left": a, "right": b}

def date_in_range(date_val: Any, min_date: Any, max_offset_days: int) -> Dict[str, Any]:
    d = _to_dt(date_val); m = _to_dt(min_date)
    ok = m <= d <= (m + timedelta(days=int(max_offset_days)))
    return {"passed": ok, "reason": f"{d} in [{m}, {m+timedelta(days=int(max_offset_days))}]" if ok else f"{d} out of range", "left": d, "right": m}

