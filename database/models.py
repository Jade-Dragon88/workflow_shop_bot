from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List

@dataclass
class User:
    telegram_id: int
    username: Optional[str] = None
    registered_at: datetime = field(default_factory=datetime.now)
    total_spent: float = 0.0
    referral_source: Optional[str] = None

@dataclass
class Workflow:
    id: Optional[int] = None
    slug: str = field(metadata={"unique": True})
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: int = 0
    price: float = 0.0
    filepath: str
    version: str = "1.0"
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    downloads: int = 0
    revenue: float = 0.0

@dataclass
class Purchase:
    id: Optional[int] = None
    user_id: int
    workflow_id: int
    price: float
    payment_id: str
    purchased_at: datetime = field(default_factory=datetime.now)
    email: Optional[str] = None
    download_count: int = 0
    last_download_at: Optional[datetime] = None
    ip_address: Optional[str] = None

@dataclass
class WorkflowUpdate:
    id: Optional[int] = None
    workflow_id: int
    version: str
    changelog: Optional[str] = None
    update_price: float = 0.0
    released_at: datetime = field(default_factory=datetime.now)

@dataclass
class InviteLink:
    id: Optional[int] = None
    workflow_id: int
    invite_link: str
    expires_at: datetime
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Settings:
    key: str = field(metadata={"unique": True})
    value: str

@dataclass
class BannedUser:
    telegram_id: int = field(metadata={"unique": True})
    reason: Optional[str] = None
    banned_at: datetime = field(default_factory=datetime.now)
    banned_by: Optional[str] = None

@dataclass
class DeliveryLog:
    id: Optional[int] = None
    user_id: int
    workflow_id: int
    status: str # e.g., "success", "failed"
    error_message: Optional[str] = None
    delivered_at: datetime = field(default_factory=datetime.now)
