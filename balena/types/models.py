from typing import Any, Dict, Optional, TypedDict


class APIKeyType(TypedDict):
    id: int
    created_at: str
    name: str
    description: Optional[str]
    expiry_date: Optional[str]
    is_of__actor: Dict[str, Any]


class APIKeyInfoType(TypedDict, total=False):
    name: Optional[str]
    description: Optional[str]
    expiry_date: Optional[str]
