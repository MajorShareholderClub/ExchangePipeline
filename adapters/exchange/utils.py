def update_dict(message: dict, key: str) -> dict:
    """dict 병합"""
    merged = message.copy()

    data_sub = message.get(key)
    if isinstance(data_sub, dict):
        merged.update(data_sub)
    elif isinstance(data_sub, list):
        merged.update(data_sub[0])

    return merged
