def create_session_payload(user_id: int, role: str) -> dict:
    return {"user_id": user_id, "role": role}
