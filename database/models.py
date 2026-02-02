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
    # Fields without default values first
    slug: str
    name: str
    filepath: str
    version: str
    
    # Fields with default values
    id: Optional[int] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: int = 0
    price: float = 0.0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    downloads: int = 0
    revenue: float = 0.0

@dataclass
class Purchase:
    # Fields without default values first
    user_id: int
    workflow_id: int
    price: float
    payment_id: str
    
    # Fields with default values
    id: Optional[int] = None
    purchased_at: datetime = field(default_factory=datetime.now)
    email: Optional[str] = None
    download_count: int = 0
    last_download_at: Optional[datetime] = None
    ip_address: Optional[str] = None

@dataclass
class WorkflowUpdate:
    # Fields without default values first
    workflow_id: int
    version: str
    
    # Fields with default values
    id: Optional[int] = None
    changelog: Optional[str] = None
    update_price: float = 0.0
    released_at: datetime = field(default_factory=datetime.now)

@dataclass
class InviteLink:
    # Fields without default values first
    workflow_id: int
    invite_link: str
    expires_at: datetime
    
    # Fields with default values
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Settings:
    key: str
    value: str

@dataclass
class BannedUser:
    telegram_id: int
    reason: Optional[str] = None
    banned_at: datetime = field(default_factory=datetime.now)
    banned_by: Optional[str] = None

@dataclass
class DeliveryLog:
    # Fields without default values first
    user_id: int
    workflow_id: int
    status: str # e.g., "success", "failed"
    
    # Fields with default values
    id: Optional[int] = None
    error_message: Optional[str] = None
    delivered_at: datetime = field(default_factory=datetime.now)