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
