def update_dict(message: dict, key: str) -> dict:
    """
    message[key]가 dict 또는 list[dict]인 경우 해당 내용을 message에 병합하여 반환
    """
    merged = message.copy()
    data_sub = message.get(key)

    if isinstance(data_sub, dict):
        merged.update(data_sub)
    elif isinstance(data_sub, list) and data_sub and isinstance(data_sub[0], dict):
        merged.update(data_sub[0])

    return merged
