# agents/compare.py (add)
def name_equals(a, b):
    from re import sub
    def clean(x): 
        return sub(r"[^A-Za-z ]","", str(x)).upper().strip()
    ca, cb = clean(a), clean(b)
    ok = ca == cb
    return {"passed": ok, "reason": f"{ca} == {cb}" if ok else f"{ca} != {cb}", "left": a, "right": b}

def compare(left, right, operation, config):
    """
    Returns: {
        "passed": bool,
        "reason": "Account numbers match after normalization",
        "left_value": "ACC12345",
        "right_value": "ACC-12345",
        "normalized_match": True
    }
    """
